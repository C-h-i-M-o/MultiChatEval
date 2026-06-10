from decimal import Decimal

import pytest

from app.core.api_keys import store_api_key
from app.models.model_config import ModelConfig, ModelProvider
from app.schemas.model_config import ModelConfigCreate, ModelConfigUpdate
from app.services.model_config_service import ModelConfigServiceError, model_config_service


class FakeDb:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.deleted: list[object] = []
        self.committed = False
        self.next_id = 1

    def add(self, item: object) -> None:
        if getattr(item, "id", None) is None:
            item.id = self.next_id
            self.next_id += 1
        self.added.append(item)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True

    async def delete(self, item: object) -> None:
        self.deleted.append(item)


def make_config(provider_name: str = "custom", config_id: int = 1) -> ModelConfig:
    provider = ModelProvider(
        id=config_id,
        name=provider_name,
        base_url="https://example.com/v1",
        api_key_encrypted=store_api_key("sk-test-1234"),
        enabled=True,
    )
    config = ModelConfig(
        id=config_id,
        provider_id=config_id,
        model_name="chat-model",
        display_name="测试模型",
        price_input=Decimal("0"),
        price_output=Decimal("0"),
        max_tokens=128,
        enabled=True,
    )
    config.provider = provider
    return config


def make_provider(provider_name: str, provider_id: int = 1, api_key: str | None = None) -> ModelProvider:
    return ModelProvider(
        id=provider_id,
        name=provider_name,
        base_url="https://example.com/v1",
        api_key_encrypted=store_api_key(api_key),
        enabled=True,
    )


def test_serialize_config_never_exposes_raw_api_key() -> None:
    config = make_config(provider_name="deepseek")

    result = model_config_service._serialize_config(config)

    assert result.has_api_key is True
    assert result.masked_api_key == "sk-t****1234"
    assert result.masked_api_key != "sk-test-1234"
    assert result.builtin is True


@pytest.mark.asyncio
async def test_list_available_configs_only_returns_enabled_configs_with_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured = make_config(provider_name="deepseek", config_id=1)
    missing_key = make_config(provider_name="minimax", config_id=2)
    missing_key.provider.api_key_encrypted = None

    async def fake_ensure_builtin_configs(_db: FakeDb) -> None:
        return None

    async def fake_list_enabled_model_configs(_db: FakeDb) -> list[ModelConfig]:
        return [configured, missing_key]

    monkeypatch.setattr(model_config_service, "ensure_builtin_configs", fake_ensure_builtin_configs)
    monkeypatch.setattr(model_config_service, "_list_enabled_model_configs", fake_list_enabled_model_configs)

    result = await model_config_service.list_available_configs(FakeDb())

    assert [item.id for item in result] == [1]
    assert result[0].display_name == "测试模型"


@pytest.mark.asyncio
async def test_update_config_keeps_old_api_key_when_payload_key_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeDb()
    config = make_config()
    original_key = config.provider.api_key_encrypted

    async def fake_get_model_config(_db: FakeDb, _model_config_id: int) -> ModelConfig:
        return config

    monkeypatch.setattr(model_config_service, "_get_model_config", fake_get_model_config)

    result = await model_config_service.update_config(
        db,
        1,
        ModelConfigUpdate(apiKey="", displayName="更新后的模型"),
    )

    assert config.provider.api_key_encrypted == original_key
    assert config.display_name == "更新后的模型"
    assert result.display_name == "更新后的模型"
    assert db.committed is True


@pytest.mark.asyncio
async def test_update_config_can_store_user_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeDb()
    config = make_config(provider_name="deepseek")
    config.provider.api_key_encrypted = None

    async def fake_get_model_config(_db: FakeDb, _model_config_id: int) -> ModelConfig:
        return config

    monkeypatch.setattr(model_config_service, "_get_model_config", fake_get_model_config)

    result = await model_config_service.update_config(
        db,
        1,
        ModelConfigUpdate(apiKey="sk-user-key", displayName="deepseek-v4-flash"),
    )

    assert config.provider.api_key_encrypted == "plain:sk-user-key"
    assert result.has_api_key is True
    assert result.masked_api_key == "sk-u****-key"


@pytest.mark.asyncio
async def test_builtin_config_cannot_be_deleted(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeDb()
    config = make_config(provider_name="glm")

    async def fake_get_model_config(_db: FakeDb, _model_config_id: int) -> ModelConfig:
        return config

    monkeypatch.setattr(model_config_service, "_get_model_config", fake_get_model_config)

    with pytest.raises(ModelConfigServiceError):
        await model_config_service.delete_config(db, 1)

    assert db.deleted == []


@pytest.mark.asyncio
async def test_resolve_runtime_models_uses_selected_enabled_config_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    deepseek_config = make_config(provider_name="deepseek", config_id=1)
    custom_config = make_config(provider_name="custom", config_id=4)
    custom_config.display_name = "自定义模型"

    async def fake_ensure_builtin_configs(_db: FakeDb) -> None:
        return None

    async def fake_list_enabled_model_configs(_db: FakeDb) -> list[ModelConfig]:
        return [deepseek_config, custom_config]

    monkeypatch.setattr(model_config_service, "ensure_builtin_configs", fake_ensure_builtin_configs)
    monkeypatch.setattr(model_config_service, "_list_enabled_model_configs", fake_list_enabled_model_configs)

    result = await model_config_service.resolve_runtime_models(FakeDb(), [4])

    assert [model.id for model in result] == [4]
    assert result[0].provider_name == "custom"
    assert result[0].display_name == "自定义模型"


@pytest.mark.asyncio
async def test_create_custom_config_marks_provider_as_plain_key(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeDb()
    captured_config: ModelConfig | None = None

    async def fake_get_provider_by_name(_db: FakeDb, _provider_name: str) -> None:
        return None

    async def fake_get_model_config(_db: FakeDb, _model_config_id: int) -> ModelConfig:
        assert captured_config is not None
        return captured_config

    original_add = db.add

    def capture_add(item: object) -> None:
        nonlocal captured_config
        original_add(item)
        if isinstance(item, ModelConfig):
            captured_config = item
            captured_config.provider = db.added[0]

    db.add = capture_add
    monkeypatch.setattr(model_config_service, "_get_provider_by_name", fake_get_provider_by_name)
    monkeypatch.setattr(model_config_service, "_get_model_config", fake_get_model_config)

    result = await model_config_service.create_config(
        db,
        ModelConfigCreate(
            providerName="custom-provider",
            displayName="自定义模型",
            modelName="custom-model",
            baseUrl="https://example.com/v1",
            apiKey="sk-custom-1234",
        ),
    )

    provider = db.added[0]
    assert isinstance(provider, ModelProvider)
    assert provider.api_key_encrypted == "plain:sk-custom-1234"
    assert result.provider_name == "custom-provider"


@pytest.mark.asyncio
async def test_ensure_builtin_configs_creates_builtin_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeDb()

    async def fake_get_provider_by_name(_db: FakeDb, _provider_name: str) -> None:
        return None

    async def fake_get_first_config_by_provider_id(_db: FakeDb, _provider_id: int) -> None:
        return None

    monkeypatch.setattr(model_config_service, "_get_provider_by_name", fake_get_provider_by_name)
    monkeypatch.setattr(model_config_service, "_get_first_config_by_provider_id", fake_get_first_config_by_provider_id)

    await model_config_service.ensure_builtin_configs(db)

    providers = [item for item in db.added if isinstance(item, ModelProvider)]
    assert [provider.name for provider in providers] == ["deepseek", "minimax", "glm"]
    assert all(provider.api_key_encrypted is None for provider in providers)
    assert db.committed is True


@pytest.mark.asyncio
async def test_ensure_builtin_configs_does_not_backfill_missing_builtin_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeDb()
    providers = {
        "deepseek": make_provider("deepseek", provider_id=1, api_key=None),
        "minimax": make_provider("minimax", provider_id=2, api_key=None),
        "glm": make_provider("glm", provider_id=3, api_key=None),
    }

    async def fake_get_provider_by_name(_db: FakeDb, provider_name: str) -> ModelProvider | None:
        return providers[provider_name]

    async def fake_get_first_config_by_provider_id(_db: FakeDb, provider_id: int) -> ModelConfig:
        return make_config(config_id=provider_id)

    monkeypatch.setattr(model_config_service, "_get_provider_by_name", fake_get_provider_by_name)
    monkeypatch.setattr(model_config_service, "_get_first_config_by_provider_id", fake_get_first_config_by_provider_id)

    await model_config_service.ensure_builtin_configs(db)

    assert all(provider.api_key_encrypted is None for provider in providers.values())
    assert db.committed is False
