import asyncio
from collections.abc import AsyncIterator
from decimal import Decimal

import pytest

from app.schemas.evaluation import EvaluationScoreRead, EvaluationTaskCreate, ModelResponseRead
from app.services.evaluation_service import evaluation_service
from app.services.model_config_service import RuntimeModelConfig, model_config_service


class FakeDb:
    pass


class FakeScalarResult:
    def __init__(self, scalar_value: object = None, rows: list[tuple[str, int]] | None = None) -> None:
        self.scalar_value = scalar_value
        self.rows = rows or []

    def scalar_one_or_none(self) -> object:
        return self.scalar_value

    def all(self) -> list[tuple[str, int]]:
        return self.rows


class FakeFeedbackDb:
    def __init__(self, execute_results: list[FakeScalarResult]) -> None:
        self.execute_results = execute_results
        self.added_objects: list[object] = []
        self.deleted_objects: list[object] = []
        self.commit_count = 0

    async def execute(self, _statement: object) -> FakeScalarResult:
        return self.execute_results.pop(0)

    def add(self, value: object) -> None:
        self.added_objects.append(value)

    async def delete(self, value: object) -> None:
        self.deleted_objects.append(value)

    async def commit(self) -> None:
        self.commit_count += 1


def make_runtime_model(model_id: int, display_name: str) -> RuntimeModelConfig:
    return RuntimeModelConfig(
        id=model_id,
        provider_name=f"provider-{model_id}",
        display_name=display_name,
        model_name=f"model-{model_id}",
        base_url="https://example.com/v1",
        api_key="sk-test",
        input_price=Decimal("0"),
        output_price=Decimal("0"),
        max_tokens=128,
        extra_body={},
    )


def make_response(
    model_id: int,
    model_name: str,
    status: str = "success",
    response_id: int | None = None,
) -> ModelResponseRead:
    return ModelResponseRead(
        id=response_id or model_id,
        modelConfigId=model_id,
        modelName=model_name,
        provider=f"provider-{model_id}",
        answer=f"{model_name} 回答",
        latencyMs=model_id * 100,
        outputTokens=10,
        estimatedCost=0,
        status=status,
        score=EvaluationScoreRead(
            relevance=8,
            completeness=8,
            clarity=8,
            format=8,
            safety=10,
            final=8.4,
        ),
    )


async def collect_events(events: AsyncIterator[dict[str, object]]) -> list[dict[str, object]]:
    collected_events = []
    async for event in events:
        collected_events.append(event)
    return collected_events


def test_thinking_extra_body_disabled_for_all_models() -> None:
    payload = EvaluationTaskCreate(prompt="你好", modelIds=[1], enableThinking=False)

    result = evaluation_service._thinking_extra_body(payload)

    assert result == {"thinking": {"type": "disabled"}}


def test_thinking_extra_body_enabled_without_effort() -> None:
    payload = EvaluationTaskCreate(prompt="你好", modelIds=[1], enableThinking=True)

    result = evaluation_service._thinking_extra_body(payload)

    assert result == {"thinking": {"type": "enabled"}}
    assert "reasoning_effort" not in result


def test_model_prompt_contains_builtin_instruction_before_user_prompt() -> None:
    result = evaluation_service._model_prompt("请解释什么是设计模式")

    assert result.startswith("你是一个严谨、清晰、负责任的 AI 助手。")
    assert "10." not in result
    assert result.endswith("请解释什么是设计模式")
    assert "用户问题如下：" in result
    assert "thinkingEffort" not in result


@pytest.mark.asyncio
async def test_stream_task_events_yields_model_responses_in_completion_order(monkeypatch: pytest.MonkeyPatch) -> None:
    models = [make_runtime_model(1, "慢模型"), make_runtime_model(2, "快模型")]

    async def fake_resolve_runtime_models(_db: FakeDb, model_ids: list[int]) -> list[RuntimeModelConfig]:
        assert model_ids == [1, 2]
        return models

    async def fake_call_model(prompt: str, model: RuntimeModelConfig, extra_body: dict[str, object]) -> ModelResponseRead:
        assert prompt == "测试问题"
        assert extra_body == {"thinking": {"type": "disabled"}}
        if model.id == 1:
            await asyncio.sleep(0.02)
        return make_response(model.id, model.display_name, response_id=model.id + 500)

    async def fake_create_task_record(_db: FakeDb, payload: EvaluationTaskCreate) -> int:
        assert payload.prompt == "测试问题"
        return 101

    async def fake_persist_response(_db: FakeDb, task_id: int, response: ModelResponseRead) -> ModelResponseRead:
        assert task_id == 101
        return response

    async def fake_finish_task_record(_db: FakeDb, task_id: int, status: str) -> None:
        assert task_id == 101
        assert status == "completed"

    monkeypatch.setattr(model_config_service, "resolve_runtime_models", fake_resolve_runtime_models)
    monkeypatch.setattr(evaluation_service, "_call_model", fake_call_model)
    monkeypatch.setattr(evaluation_service, "_create_task_record", fake_create_task_record, raising=False)
    monkeypatch.setattr(evaluation_service, "_persist_response", fake_persist_response, raising=False)
    monkeypatch.setattr(evaluation_service, "_finish_task_record", fake_finish_task_record, raising=False)

    events = await collect_events(
        evaluation_service.stream_task_events(
            EvaluationTaskCreate(prompt="测试问题", modelIds=[1, 2], enableThinking=False),
            FakeDb(),
        )
    )

    assert [event["type"] for event in events] == [
        "task_started",
        "model_response",
        "model_response",
        "task_completed",
    ]
    assert events[0]["taskId"] == 101
    assert events[0]["modelIds"] == [1, 2]
    assert events[1]["response"].model_name == "快模型"
    assert events[1]["response"].id == 502
    assert events[1]["response"].model_config_id == 2
    assert events[2]["response"].model_name == "慢模型"
    assert events[2]["response"].id == 501
    assert events[2]["response"].model_config_id == 1
    assert events[3]["task"].task_id == 101
    assert events[3]["task"].status == "completed"


@pytest.mark.asyncio
async def test_stream_task_events_keeps_running_when_one_model_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    models = [make_runtime_model(1, "失败模型"), make_runtime_model(2, "成功模型")]

    async def fake_resolve_runtime_models(_db: FakeDb, _model_ids: list[int]) -> list[RuntimeModelConfig]:
        return models

    async def fake_call_model(prompt: str, model: RuntimeModelConfig, extra_body: dict[str, object]) -> ModelResponseRead:
        assert prompt == "测试问题"
        assert extra_body == {"thinking": {"type": "enabled"}}
        status = "failed" if model.id == 1 else "success"
        return make_response(model.id, model.display_name, status=status)

    async def fake_create_task_record(_db: FakeDb, _payload: EvaluationTaskCreate) -> int:
        return 102

    async def fake_persist_response(_db: FakeDb, _task_id: int, response: ModelResponseRead) -> ModelResponseRead:
        return response

    async def fake_finish_task_record(_db: FakeDb, task_id: int, status: str) -> None:
        assert task_id == 102
        assert status == "completed"

    monkeypatch.setattr(model_config_service, "resolve_runtime_models", fake_resolve_runtime_models)
    monkeypatch.setattr(evaluation_service, "_call_model", fake_call_model)
    monkeypatch.setattr(evaluation_service, "_create_task_record", fake_create_task_record, raising=False)
    monkeypatch.setattr(evaluation_service, "_persist_response", fake_persist_response, raising=False)
    monkeypatch.setattr(evaluation_service, "_finish_task_record", fake_finish_task_record, raising=False)

    events = await collect_events(
        evaluation_service.stream_task_events(
            EvaluationTaskCreate(prompt="测试问题", modelIds=[1, 2], enableThinking=True),
            FakeDb(),
        )
    )

    responses = [event["response"] for event in events if event["type"] == "model_response"]

    assert [response.status for response in responses] == ["failed", "success"]
    assert events[-1]["task"].status == "completed"


@pytest.mark.asyncio
async def test_create_task_persists_task_responses_and_scores(monkeypatch: pytest.MonkeyPatch) -> None:
    models = [make_runtime_model(3, "持久化模型")]
    persisted_response_ids = []

    async def fake_resolve_runtime_models(_db: FakeDb, _model_ids: list[int]) -> list[RuntimeModelConfig]:
        return models

    async def fake_call_model(prompt: str, model: RuntimeModelConfig, extra_body: dict[str, object]) -> ModelResponseRead:
        assert prompt == "需要保存的问题"
        assert extra_body == {"thinking": {"type": "disabled"}}
        return make_response(model.id, model.display_name, response_id=700)

    async def fake_create_task_record(_db: FakeDb, payload: EvaluationTaskCreate) -> int:
        assert payload.prompt == "需要保存的问题"
        return 200

    async def fake_persist_response(_db: FakeDb, task_id: int, response: ModelResponseRead) -> ModelResponseRead:
        assert task_id == 200
        persisted_response_ids.append(response.id)
        return response

    async def fake_finish_task_record(_db: FakeDb, task_id: int, status: str) -> None:
        assert task_id == 200
        assert status == "completed"

    monkeypatch.setattr(model_config_service, "resolve_runtime_models", fake_resolve_runtime_models)
    monkeypatch.setattr(evaluation_service, "_call_model", fake_call_model)
    monkeypatch.setattr(evaluation_service, "_create_task_record", fake_create_task_record, raising=False)
    monkeypatch.setattr(evaluation_service, "_persist_response", fake_persist_response, raising=False)
    monkeypatch.setattr(evaluation_service, "_finish_task_record", fake_finish_task_record, raising=False)

    task = await evaluation_service.create_task(
        EvaluationTaskCreate(prompt="需要保存的问题", modelIds=[3]),
        FakeDb(),
    )

    assert task.task_id == 200
    assert task.status == "completed"
    assert task.responses[0].id == 700
    assert task.responses[0].model_config_id == 3
    assert persisted_response_ids == [700]


@pytest.mark.asyncio
async def test_toggle_feedback_creates_feedback_when_inactive() -> None:
    db = FakeFeedbackDb(
        [
            FakeScalarResult(scalar_value=5001),
            FakeScalarResult(scalar_value=None),
            FakeScalarResult(rows=[("like", 1)]),
        ]
    )

    result = await evaluation_service.toggle_feedback(5001, "like", None, db)

    assert result.response_id == 5001
    assert result.feedback_type == "like"
    assert result.active is True
    assert result.feedback.liked is True
    assert result.feedback.like_count == 1
    assert len(db.added_objects) == 1
    assert db.deleted_objects == []
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_toggle_feedback_deletes_feedback_when_active() -> None:
    existing_feedback = object()
    db = FakeFeedbackDb(
        [
            FakeScalarResult(scalar_value=5001),
            FakeScalarResult(scalar_value=existing_feedback),
            FakeScalarResult(rows=[]),
        ]
    )

    result = await evaluation_service.toggle_feedback(5001, "accepted", None, db)

    assert result.response_id == 5001
    assert result.feedback_type == "accepted"
    assert result.active is False
    assert result.feedback.accepted is False
    assert db.added_objects == []
    assert db.deleted_objects == [existing_feedback]
    assert db.commit_count == 1
