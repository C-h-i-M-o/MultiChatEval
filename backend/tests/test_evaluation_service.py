import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.evaluation import (
    CommentCreate,
    EvaluationFeedbackRead,
    EvaluationScoreRead,
    EvaluationTaskCreate,
    FeedbackCreate,
    ModelResponseRead,
)
from app.models.evaluation import EvaluationResult, EvaluationTask
from app.models.comment import UserComment
from app.models.feedback import UserFeedback
from app.models.response import ModelResponse
from app.services.evaluation_service import (
    EvaluationCommentNotFoundError,
    EvaluationResponseNotFoundError,
    evaluation_service,
)
from app.services.llm_judge_evaluator import LLMJudgeResult, llm_judge_evaluator
from app.services.model_config_service import RuntimeModelConfig, model_config_service


class FakeDb:
    pass


class FakeScalarResult:
    def __init__(self, items: list[object]) -> None:
        self.items = items

    def scalar_one_or_none(self) -> object | None:
        return self.items[0] if self.items else None

    def scalar_one(self) -> object:
        return self.items[0]

    def scalars(self) -> "FakeScalarResult":
        return self

    def all(self) -> list[object]:
        return self.items


class FakeFeedbackDb:
    def __init__(
        self,
        response_exists: bool = True,
        feedback_records: list[UserFeedback] | None = None,
        judge_score: Decimal | None = None,
    ) -> None:
        self.response_exists = response_exists
        self.feedback_records = feedback_records or []
        self.committed = False
        self.response = ModelResponse(
            id=44,
            task_id=1,
            answer_text="测试回答",
            status="success",
            evaluation_result=EvaluationResult(
                relevance_score=Decimal("8"),
                completeness_score=Decimal("8"),
                clarity_score=Decimal("8"),
                format_score=Decimal("8"),
                safety_score=Decimal("10"),
                rule_score=Decimal("8.4"),
                judge_score=judge_score,
                final_score=Decimal("8.4"),
            ),
        )
        self.response.task = EvaluationTask(id=1, prompt="测试问题", status="completed")

    async def execute(self, statement: object) -> FakeScalarResult:
        entity = statement.column_descriptions[0].get("entity")
        if entity is UserFeedback:
            return FakeScalarResult(sorted(self.feedback_records, key=lambda feedback: feedback.id or 0))
        if entity is ModelResponse:
            return FakeScalarResult([self.response] if self.response_exists else [])
        return FakeScalarResult([])

    def add(self, feedback: UserFeedback) -> None:
        feedback.id = len(self.feedback_records) + 1
        self.feedback_records.append(feedback)

    async def delete(self, feedback: UserFeedback) -> None:
        self.feedback_records = [item for item in self.feedback_records if item is not feedback]

    async def commit(self) -> None:
        self.committed = True

    async def flush(self) -> None:
        pass


class FakeCreateCommentDb:
    def __init__(self, response_exists: bool = True) -> None:
        self.response_exists = response_exists
        self.comment: UserComment | None = None
        self.committed = False

    async def execute(self, _statement: object) -> FakeScalarResult:
        return FakeScalarResult([44] if self.response_exists else [])

    def add(self, comment: UserComment) -> None:
        self.comment = comment

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, comment: UserComment) -> None:
        comment.id = 301
        comment.created_at = datetime(2026, 6, 6, 10, 30, 0)


class FakeDeleteCommentDb:
    def __init__(self, comment: UserComment | None) -> None:
        self.comment = comment
        self.deleted = False
        self.committed = False

    async def execute(self, _statement: object) -> FakeScalarResult:
        return FakeScalarResult([self.comment] if self.comment is not None else [])

    async def delete(self, _comment: UserComment) -> None:
        self.deleted = True

    async def commit(self) -> None:
        self.committed = True


class FakeListCommentDb:
    def __init__(self, comments: list[tuple[UserComment, str]]) -> None:
        self.comments = comments
        self.execute_count = 0

    async def execute(self, _statement: object) -> FakeScalarResult:
        self.execute_count += 1
        if self.execute_count == 1:
            return FakeScalarResult([44])
        if self.execute_count == 2:
            return FakeScalarResult([len(self.comments)])
        return FakeScalarResult(self.comments)


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
    assert "保持中文表达清晰、自然、结构化" in result
    assert "thinkingEffort" not in result
    assert result.endswith("请解释什么是设计模式")


def test_enable_judge_requires_judge_model_id() -> None:
    with pytest.raises(ValidationError):
        EvaluationTaskCreate(prompt="你好", modelIds=[1], enableJudge=True)


def test_feedback_create_allows_like_and_dislike_only() -> None:
    assert FeedbackCreate(feedbackType="like").feedback_type == "like"
    assert FeedbackCreate(feedbackType="dislike").feedback_type == "dislike"

    with pytest.raises(ValidationError):
        FeedbackCreate(feedbackType="accepted")


def test_comment_create_strips_content_and_validates_length() -> None:
    assert CommentCreate(content="  有帮助  ").content == "有帮助"

    with pytest.raises(ValidationError):
        CommentCreate(content="   ")
    with pytest.raises(ValidationError):
        CommentCreate(content="评" * 1001)


def test_score_defaults_rule_final_to_final_without_judge() -> None:
    score = EvaluationScoreRead(
        relevance=8,
        completeness=8,
        clarity=8,
        format=8,
        safety=10,
        final=8.4,
    )

    assert score.rule_final == 8.4
    assert score.judge_final is None
    assert score.base_final == 8.4


def test_serialize_score_rebuilds_rule_details_for_history() -> None:
    result = EvaluationResult(
        relevance_score=Decimal("8"),
        completeness_score=Decimal("8"),
        clarity_score=Decimal("8"),
        format_score=Decimal("8"),
        safety_score=Decimal("10"),
        rule_score=Decimal("8.4"),
        final_score=Decimal("8.4"),
    )

    score = evaluation_service._serialize_score(
        result,
        prompt="请用表格解释设计模式",
        answer="设计模式|作用\n---|---\n工厂模式|创建对象",
    )

    assert score.details["format"]


def test_serialize_feedback_uses_anonymous_user_state_and_counts() -> None:
    feedback = evaluation_service._serialize_feedback(
        [
            UserFeedback(id=1, user_id=0, response_id=44, feedback_type="like"),
            UserFeedback(id=2, user_id=2, response_id=44, feedback_type="like"),
            UserFeedback(id=3, user_id=3, response_id=44, feedback_type="dislike"),
        ]
    )

    assert feedback.liked is True
    assert feedback.disliked is False
    assert feedback.like_count == 2
    assert feedback.dislike_count == 1


@pytest.mark.asyncio
async def test_toggle_response_feedback_creates_anonymous_like() -> None:
    db = FakeFeedbackDb()

    result = await evaluation_service.toggle_response_feedback(44, FeedbackCreate(feedbackType="like"), db)

    assert result.active is True
    assert result.feedback.liked is True
    assert result.feedback.like_count == 1
    assert result.score.base_final == 8.4
    assert result.score.feedback_score == 10
    assert result.score.final == 8.56
    assert db.response.evaluation_result.final_score == Decimal("8.56")
    assert db.feedback_records[0].user_id == 0
    assert db.feedback_records[0].feedback_type == "like"
    assert db.committed is True


@pytest.mark.asyncio
async def test_toggle_response_feedback_cancels_same_type() -> None:
    db = FakeFeedbackDb(
        feedback_records=[UserFeedback(id=1, user_id=0, response_id=44, feedback_type="like")]
    )

    result = await evaluation_service.toggle_response_feedback(44, FeedbackCreate(feedbackType="like"), db)

    assert result.active is False
    assert result.feedback.liked is False
    assert result.feedback.like_count == 0
    assert result.score.feedback_score is None
    assert result.score.final == 8.4
    assert db.feedback_records == []


@pytest.mark.asyncio
async def test_toggle_response_feedback_switches_between_like_and_dislike() -> None:
    db = FakeFeedbackDb(
        feedback_records=[UserFeedback(id=1, user_id=0, response_id=44, feedback_type="dislike")]
    )

    result = await evaluation_service.toggle_response_feedback(44, FeedbackCreate(feedbackType="like"), db)

    assert result.active is True
    assert result.feedback.liked is True
    assert result.feedback.disliked is False
    assert result.feedback.like_count == 1
    assert result.feedback.dislike_count == 0
    assert result.score.final == 8.56
    assert len(db.feedback_records) == 1
    assert db.feedback_records[0].feedback_type == "like"


@pytest.mark.asyncio
async def test_toggle_response_feedback_requires_existing_response() -> None:
    db = FakeFeedbackDb(response_exists=False)

    with pytest.raises(EvaluationResponseNotFoundError):
        await evaluation_service.toggle_response_feedback(44, FeedbackCreate(feedbackType="like"), db)


def test_feedback_score_uses_like_ratio() -> None:
    feedback = EvaluationFeedbackRead(likeCount=3, dislikeCount=1)

    assert evaluation_service._feedback_score(feedback) == 7.5
    assert evaluation_service._feedback_score(EvaluationFeedbackRead()) is None


def test_recalculate_final_score_uses_judge_base_and_feedback_weight() -> None:
    db = FakeFeedbackDb(judge_score=Decimal("9.0"))
    feedback = EvaluationFeedbackRead(likeCount=3, dislikeCount=1)

    score = evaluation_service._recalculate_final_score(db.response, feedback)

    assert score.base_final == 8.64
    assert score.feedback_score == 7.5
    assert score.final == 8.53
    assert db.response.evaluation_result.final_score == Decimal("8.53")


@pytest.mark.asyncio
async def test_create_response_comment_persists_trimmed_content() -> None:
    db = FakeCreateCommentDb()

    result = await evaluation_service.create_response_comment(
        44,
        CommentCreate(content="  评论内容  "),
        db,
    )

    assert result.id == 301
    assert result.content == "评论内容"
    assert result.can_delete is True
    assert db.comment is not None
    assert db.comment.user_id == 0
    assert db.committed is True


@pytest.mark.asyncio
async def test_create_response_comment_requires_existing_response() -> None:
    db = FakeCreateCommentDb(response_exists=False)

    with pytest.raises(EvaluationResponseNotFoundError):
        await evaluation_service.create_response_comment(404, CommentCreate(content="评论内容"), db)


@pytest.mark.asyncio
async def test_list_response_comments_returns_latest_page() -> None:
    created_at = datetime(2026, 6, 6, 10, 30, 0)
    comment = UserComment(
        id=301,
        user_id=0,
        response_id=44,
        content="评论内容",
        created_at=created_at,
    )
    db = FakeListCommentDb([(comment, "anonymous")])

    result = await evaluation_service.list_response_comments(44, db, page=2, page_size=10)

    assert result.total == 1
    assert result.page == 2
    assert result.page_size == 10
    assert result.items[0].content == "评论内容"


@pytest.mark.asyncio
async def test_delete_response_comment_deletes_owned_comment() -> None:
    comment = UserComment(id=301, user_id=0, response_id=44, content="评论内容")
    db = FakeDeleteCommentDb(comment)

    await evaluation_service.delete_response_comment(301, db)

    assert db.deleted is True
    assert db.committed is True


@pytest.mark.asyncio
async def test_delete_response_comment_requires_owned_comment() -> None:
    db = FakeDeleteCommentDb(None)

    with pytest.raises(EvaluationCommentNotFoundError):
        await evaluation_service.delete_response_comment(404, db)


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
async def test_create_task_applies_judge_score_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    models = [make_runtime_model(3, "被评测模型")]
    judge_model = make_runtime_model(9, "评审模型")
    persisted_scores = []

    async def fake_resolve_runtime_models(_db: FakeDb, model_ids: list[int]) -> list[RuntimeModelConfig]:
        assert model_ids == [3]
        return models

    async def fake_resolve_runtime_model(_db: FakeDb, model_id: int) -> RuntimeModelConfig:
        assert model_id == 9
        return judge_model

    async def fake_call_model(prompt: str, model: RuntimeModelConfig, extra_body: dict[str, object]) -> ModelResponseRead:
        assert prompt == "需要评审的问题"
        assert extra_body == {"thinking": {"type": "disabled"}}
        return make_response(model.id, model.display_name, response_id=700)

    async def fake_judge(prompt: str, answer: str, model: RuntimeModelConfig) -> LLMJudgeResult:
        assert prompt == "需要评审的问题"
        assert answer == "被评测模型 回答"
        assert model.id == 9
        return LLMJudgeResult(
            score=9.0,
            comment="优点：覆盖充分；缺点：示例略少；建议：可以补充示例。",
            details={
                "strengths": ["覆盖充分"],
                "weaknesses": ["示例略少"],
                "recommendation": ["可以补充示例"],
            },
        )

    async def fake_create_task_record(_db: FakeDb, _payload: EvaluationTaskCreate) -> int:
        return 200

    async def fake_persist_response(_db: FakeDb, _task_id: int, response: ModelResponseRead) -> ModelResponseRead:
        persisted_scores.append(response.score)
        return response

    async def fake_finish_task_record(_db: FakeDb, _task_id: int, _status: str) -> None:
        return None

    monkeypatch.setattr(model_config_service, "resolve_runtime_models", fake_resolve_runtime_models)
    monkeypatch.setattr(model_config_service, "resolve_runtime_model", fake_resolve_runtime_model, raising=False)
    monkeypatch.setattr(evaluation_service, "_call_model", fake_call_model)
    monkeypatch.setattr(llm_judge_evaluator, "evaluate", fake_judge)
    monkeypatch.setattr(evaluation_service, "_create_task_record", fake_create_task_record, raising=False)
    monkeypatch.setattr(evaluation_service, "_persist_response", fake_persist_response, raising=False)
    monkeypatch.setattr(evaluation_service, "_finish_task_record", fake_finish_task_record, raising=False)

    task = await evaluation_service.create_task(
        EvaluationTaskCreate(prompt="需要评审的问题", modelIds=[3], enableJudge=True, judgeModelId=9),
        FakeDb(),
    )

    assert task.responses[0].score.rule_final == 8.4
    assert task.responses[0].score.judge_final == 9.0
    assert task.responses[0].score.base_final == 8.64
    assert task.responses[0].score.final == 8.64
    assert task.responses[0].score.judge_comment == "优点：覆盖充分；缺点：示例略少；建议：可以补充示例。"
    assert persisted_scores[0].final == 8.64


@pytest.mark.asyncio
async def test_create_task_keeps_rule_score_when_judge_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    models = [make_runtime_model(3, "被评测模型")]
    judge_model = make_runtime_model(9, "评审模型")

    async def fake_resolve_runtime_models(_db: FakeDb, _model_ids: list[int]) -> list[RuntimeModelConfig]:
        return models

    async def fake_resolve_runtime_model(_db: FakeDb, _model_id: int) -> RuntimeModelConfig:
        return judge_model

    async def fake_call_model(prompt: str, model: RuntimeModelConfig, extra_body: dict[str, object]) -> ModelResponseRead:
        assert prompt == "需要评审的问题"
        assert extra_body == {"thinking": {"type": "disabled"}}
        return make_response(model.id, model.display_name, response_id=700)

    async def fake_judge(prompt: str, answer: str, model: RuntimeModelConfig) -> LLMJudgeResult:
        assert prompt == "需要评审的问题"
        assert answer == "被评测模型 回答"
        assert model.id == 9
        return LLMJudgeResult(score=None, comment="LLM 评审失败：返回内容不是合法 JSON", details={})

    async def fake_create_task_record(_db: FakeDb, _payload: EvaluationTaskCreate) -> int:
        return 200

    async def fake_persist_response(_db: FakeDb, _task_id: int, response: ModelResponseRead) -> ModelResponseRead:
        return response

    async def fake_finish_task_record(_db: FakeDb, _task_id: int, _status: str) -> None:
        return None

    monkeypatch.setattr(model_config_service, "resolve_runtime_models", fake_resolve_runtime_models)
    monkeypatch.setattr(model_config_service, "resolve_runtime_model", fake_resolve_runtime_model, raising=False)
    monkeypatch.setattr(evaluation_service, "_call_model", fake_call_model)
    monkeypatch.setattr(llm_judge_evaluator, "evaluate", fake_judge)
    monkeypatch.setattr(evaluation_service, "_create_task_record", fake_create_task_record, raising=False)
    monkeypatch.setattr(evaluation_service, "_persist_response", fake_persist_response, raising=False)
    monkeypatch.setattr(evaluation_service, "_finish_task_record", fake_finish_task_record, raising=False)

    task = await evaluation_service.create_task(
        EvaluationTaskCreate(prompt="需要评审的问题", modelIds=[3], enableJudge=True, judgeModelId=9),
        FakeDb(),
    )

    assert task.responses[0].score.final == 8.4
    assert task.responses[0].score.rule_final == 8.4
    assert task.responses[0].score.judge_final is None
    assert task.responses[0].score.judge_comment == "LLM 评审失败：返回内容不是合法 JSON"
