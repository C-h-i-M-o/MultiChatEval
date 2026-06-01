import asyncio
from dataclasses import dataclass
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.adapters.base import ModelRequest
from app.adapters.openai_compatible import OpenAICompatibleClient
from app.core.api_keys import has_stored_api_key, load_api_key, mask_stored_api_key, store_api_key
from app.core.config import settings
from app.models.model_config import ModelConfig, ModelProvider
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigRead,
    ModelConfigTestRequest,
    ModelConfigTestResult,
    ModelConfigUpdate,
)

BUILTIN_PROVIDER_NAMES = {"deepseek", "minimax", "glm"}
DEFAULT_PROVIDER_NAMES = ("deepseek", "minimax")


@dataclass(frozen=True)
class BuiltinModelDefinition:
    provider_name: str
    display_name: str
    model_name: str
    base_url: str


@dataclass(frozen=True)
class RuntimeModelConfig:
    id: int
    provider_name: str
    display_name: str
    model_name: str
    base_url: str
    api_key: str
    input_price: Decimal
    output_price: Decimal
    max_tokens: int
    extra_body: dict[str, object]


class ModelConfigServiceError(Exception):
    pass


class ModelConfigNotFoundError(ModelConfigServiceError):
    pass


class ModelConfigService:
    async def list_configs(self, db: AsyncSession) -> list[ModelConfigRead]:
        await self.ensure_builtin_configs(db)
        configs = await self._list_model_configs(db)
        return [self._serialize_config(config) for config in configs]

    async def create_config(self, db: AsyncSession, payload: ModelConfigCreate) -> ModelConfigRead:
        provider_name = self._required_text(payload.provider_name, "供应商名称")
        if provider_name in BUILTIN_PROVIDER_NAMES:
            raise ModelConfigServiceError("内置供应商配置已存在，不能重复创建")

        existing_provider = await self._get_provider_by_name(db, provider_name)
        if existing_provider is not None:
            raise ModelConfigServiceError("供应商名称已存在")

        provider = ModelProvider(
            name=provider_name,
            base_url=self._required_text(payload.base_url, "Base URL"),
            api_key_encrypted=store_api_key(payload.api_key),
            enabled=payload.enabled,
        )
        db.add(provider)
        await db.flush()

        config = ModelConfig(
            provider_id=provider.id,
            model_name=self._required_text(payload.model_name, "模型名"),
            display_name=self._required_text(payload.display_name, "展示名"),
            price_input=Decimal(str(payload.price_input)),
            price_output=Decimal(str(payload.price_output)),
            max_tokens=payload.max_tokens,
            enabled=payload.enabled,
        )
        db.add(config)
        await db.commit()
        created_config = await self._get_model_config(db, config.id)
        return self._serialize_config(created_config)

    async def update_config(self, db: AsyncSession, model_config_id: int, payload: ModelConfigUpdate) -> ModelConfigRead:
        config = await self._get_model_config(db, model_config_id)
        provider = config.provider
        builtin = self._is_builtin(provider.name)

        if payload.provider_name is not None:
            provider_name = self._required_text(payload.provider_name, "供应商名称")
            if builtin and provider_name != provider.name:
                raise ModelConfigServiceError("内置供应商名称不能修改")
            if not builtin and provider_name != provider.name:
                if provider_name in BUILTIN_PROVIDER_NAMES:
                    raise ModelConfigServiceError("自定义配置不能使用内置供应商名称")
                existing_provider = await self._get_provider_by_name(db, provider_name)
                if existing_provider is not None:
                    raise ModelConfigServiceError("供应商名称已存在")
                provider.name = provider_name

        if payload.base_url is not None:
            provider.base_url = self._required_text(payload.base_url, "Base URL")
        if payload.api_key is not None and payload.api_key.strip():
            provider.api_key_encrypted = store_api_key(payload.api_key)
        if payload.enabled is not None:
            provider.enabled = payload.enabled
            config.enabled = payload.enabled
        if payload.display_name is not None:
            config.display_name = self._required_text(payload.display_name, "展示名")
        if payload.model_name is not None:
            config.model_name = self._required_text(payload.model_name, "模型名")
        if payload.max_tokens is not None:
            config.max_tokens = payload.max_tokens
        if payload.price_input is not None:
            config.price_input = Decimal(str(payload.price_input))
        if payload.price_output is not None:
            config.price_output = Decimal(str(payload.price_output))

        await db.commit()
        updated_config = await self._get_model_config(db, model_config_id)
        return self._serialize_config(updated_config)

    async def delete_config(self, db: AsyncSession, model_config_id: int) -> None:
        config = await self._get_model_config(db, model_config_id)
        provider = config.provider
        if self._is_builtin(provider.name):
            raise ModelConfigServiceError("内置模型配置不能删除，请改为禁用")

        await db.delete(config)
        await db.delete(provider)
        await db.commit()

    async def test_config(self, db: AsyncSession, payload: ModelConfigTestRequest) -> ModelConfigTestResult:
        try:
            runtime_config = await self._resolve_test_config(db, payload)
            client = OpenAICompatibleClient(
                model_name=runtime_config.model_name,
                base_url=runtime_config.base_url,
                api_key=runtime_config.api_key,
                timeout=min(settings.model_request_timeout, 30),
                extra_body=runtime_config.extra_body,
            )
            reply = await asyncio.wait_for(
                client.chat(
                    ModelRequest(
                        prompt="请用一句话回复：连接测试成功",
                        model_name=runtime_config.model_name,
                        max_tokens=min(runtime_config.max_tokens, 64),
                    )
                ),
                timeout=min(settings.model_request_timeout + 5, 35),
            )
        except (TimeoutError, httpx.HTTPError, ValueError, KeyError, IndexError, ModelConfigServiceError) as error:
            return ModelConfigTestResult(success=False, message=f"连接测试失败：{error}", latencyMs=0)

        return ModelConfigTestResult(success=True, message="连接测试成功", latencyMs=reply.latency_ms)

    async def resolve_runtime_models(self, db: AsyncSession, model_ids: list[int]) -> list[RuntimeModelConfig]:
        await self.ensure_builtin_configs(db)
        configs = await self._list_enabled_model_configs(db)
        if not configs:
            return []

        configs_by_id = {config.id: config for config in configs}
        selected_configs = [configs_by_id[model_id] for model_id in model_ids if model_id in configs_by_id]
        if not selected_configs:
            selected_configs = self._default_model_configs(configs)

        return [self._to_runtime_config(config) for config in selected_configs]

    async def ensure_builtin_configs(self, db: AsyncSession) -> None:
        changed = False
        for definition in self._builtin_definitions():
            provider = await self._get_provider_by_name(db, definition.provider_name)
            if provider is None:
                provider = ModelProvider(
                    name=definition.provider_name,
                    base_url=definition.base_url,
                    api_key_encrypted=None,
                    enabled=True,
                )
                db.add(provider)
                await db.flush()
                changed = True
            else:
                if not provider.base_url:
                    provider.base_url = definition.base_url
                    changed = True

            config = await self._get_first_config_by_provider_id(db, provider.id)
            if config is None:
                db.add(
                    ModelConfig(
                        provider_id=provider.id,
                        model_name=definition.model_name,
                        display_name=definition.display_name,
                        price_input=Decimal("0"),
                        price_output=Decimal("0"),
                        max_tokens=1024,
                        enabled=True,
                    )
                )
                changed = True

        if changed:
            await db.commit()

    async def _resolve_test_config(self, db: AsyncSession, payload: ModelConfigTestRequest) -> RuntimeModelConfig:
        if payload.model_config_id is not None:
            config = await self._get_model_config(db, payload.model_config_id)
            runtime_config = self._to_runtime_config(config)
            provider_name = payload.provider_name.strip() if payload.provider_name and payload.provider_name.strip() else runtime_config.provider_name
            model_name = payload.model_name.strip() if payload.model_name and payload.model_name.strip() else runtime_config.model_name
            base_url = payload.base_url.strip() if payload.base_url and payload.base_url.strip() else runtime_config.base_url
            api_key = payload.api_key.strip() if payload.api_key and payload.api_key.strip() else runtime_config.api_key
            return RuntimeModelConfig(
                id=runtime_config.id,
                provider_name=provider_name,
                display_name=runtime_config.display_name,
                model_name=model_name,
                base_url=base_url,
                api_key=api_key,
                input_price=runtime_config.input_price,
                output_price=runtime_config.output_price,
                max_tokens=payload.max_tokens,
                extra_body=self._extra_body_for_provider(provider_name),
            )

        provider_name = self._required_text(payload.provider_name, "供应商名称")
        return RuntimeModelConfig(
            id=0,
            provider_name=provider_name,
            display_name=payload.model_name or provider_name,
            model_name=self._required_text(payload.model_name, "模型名"),
            base_url=self._required_text(payload.base_url, "Base URL"),
            api_key=self._required_text(payload.api_key, "API Key"),
            input_price=Decimal("0"),
            output_price=Decimal("0"),
            max_tokens=payload.max_tokens,
            extra_body=self._extra_body_for_provider(provider_name),
        )

    async def _list_model_configs(self, db: AsyncSession) -> list[ModelConfig]:
        result = await db.execute(
            select(ModelConfig).options(selectinload(ModelConfig.provider)).order_by(ModelConfig.id)
        )
        return list(result.scalars().all())

    async def _list_enabled_model_configs(self, db: AsyncSession) -> list[ModelConfig]:
        result = await db.execute(
            select(ModelConfig)
            .join(ModelConfig.provider)
            .options(selectinload(ModelConfig.provider))
            .where(ModelConfig.enabled.is_(True), ModelProvider.enabled.is_(True))
            .order_by(ModelConfig.id)
        )
        return list(result.scalars().all())

    async def _get_model_config(self, db: AsyncSession, model_config_id: int) -> ModelConfig:
        result = await db.execute(
            select(ModelConfig)
            .options(selectinload(ModelConfig.provider))
            .where(ModelConfig.id == model_config_id)
        )
        config = result.scalar_one_or_none()
        if config is None:
            raise ModelConfigNotFoundError("模型配置不存在")
        return config

    async def _get_provider_by_name(self, db: AsyncSession, provider_name: str) -> ModelProvider | None:
        result = await db.execute(select(ModelProvider).where(ModelProvider.name == provider_name))
        return result.scalar_one_or_none()

    async def _get_first_config_by_provider_id(self, db: AsyncSession, provider_id: int) -> ModelConfig | None:
        result = await db.execute(
            select(ModelConfig).where(ModelConfig.provider_id == provider_id).order_by(ModelConfig.id)
        )
        return result.scalars().first()

    def _serialize_config(self, config: ModelConfig) -> ModelConfigRead:
        provider = config.provider
        stored_key = provider.api_key_encrypted
        return ModelConfigRead(
            id=config.id,
            providerName=provider.name,
            displayName=config.display_name,
            modelName=config.model_name,
            baseUrl=provider.base_url or "",
            enabled=bool(provider.enabled and config.enabled),
            builtin=self._is_builtin(provider.name),
            hasApiKey=has_stored_api_key(stored_key),
            maskedApiKey=mask_stored_api_key(stored_key),
            maxTokens=config.max_tokens,
            priceInput=float(config.price_input),
            priceOutput=float(config.price_output),
        )

    def _to_runtime_config(self, config: ModelConfig) -> RuntimeModelConfig:
        provider = config.provider
        return RuntimeModelConfig(
            id=config.id,
            provider_name=provider.name,
            display_name=config.display_name,
            model_name=config.model_name,
            base_url=provider.base_url or "",
            api_key=load_api_key(provider.api_key_encrypted),
            input_price=Decimal(config.price_input),
            output_price=Decimal(config.price_output),
            max_tokens=config.max_tokens,
            extra_body=self._extra_body_for_provider(provider.name),
        )

    def _default_model_configs(self, configs: list[ModelConfig]) -> list[ModelConfig]:
        default_configs = [config for config in configs if config.provider.name in DEFAULT_PROVIDER_NAMES]
        if default_configs:
            return default_configs[:2]
        return configs[:2]

    def _builtin_definitions(self) -> list[BuiltinModelDefinition]:
        return [
            BuiltinModelDefinition(
                provider_name="deepseek",
                display_name=settings.deepseek_model,
                model_name=settings.deepseek_model,
                base_url=settings.deepseek_base_url,
            ),
            BuiltinModelDefinition(
                provider_name="minimax",
                display_name=settings.minimax_model,
                model_name=settings.minimax_model,
                base_url=settings.minimax_base_url,
            ),
            BuiltinModelDefinition(
                provider_name="glm",
                display_name=settings.zhipu_model,
                model_name=settings.zhipu_model,
                base_url=settings.zhipu_base_url,
            ),
        ]

    def _extra_body_for_provider(self, provider_name: str) -> dict[str, object]:
        if provider_name == "glm":
            return {"thinking": {"type": "disabled"}}
        return {}

    def _required_text(self, value: str | None, field_name: str) -> str:
        if value is None:
            raise ModelConfigServiceError(f"{field_name}不能为空")
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ModelConfigServiceError(f"{field_name}不能为空")
        return cleaned_value

    def _is_builtin(self, provider_name: str) -> bool:
        return provider_name in BUILTIN_PROVIDER_NAMES


model_config_service = ModelConfigService()
