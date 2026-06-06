from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class EvaluationTaskCreate(BaseModel):
    conversation_id: int | None = Field(default=None, alias="conversationId")
    prompt: str
    model_ids: list[int] = Field(default_factory=list, alias="modelIds")
    enable_judge: bool = Field(default=False, alias="enableJudge")
    judge_model_id: int | None = Field(default=None, alias="judgeModelId")
    enable_thinking: bool = Field(default=False, alias="enableThinking")

    @model_validator(mode="after")
    def require_judge_model(self) -> "EvaluationTaskCreate":
        if self.enable_judge and self.judge_model_id is None:
            raise ValueError("启用 LLM 评审时必须选择评审模型")
        return self


class EvaluationScoreRead(BaseModel):
    relevance: float
    completeness: float
    clarity: float
    format: float
    safety: float
    final: float
    details: dict[str, list[str]] = Field(default_factory=dict)
    rule_final: float | None = Field(default=None, alias="ruleFinal")
    judge_final: float | None = Field(default=None, alias="judgeFinal")
    base_final: float | None = Field(default=None, alias="baseFinal")
    feedback_score: float | None = Field(default=None, alias="feedbackScore")
    judge_comment: str | None = Field(default=None, alias="judgeComment")
    judge_details: dict[str, list[str]] = Field(default_factory=dict, alias="judgeDetails")

    @model_validator(mode="after")
    def default_rule_final(self) -> "EvaluationScoreRead":
        if self.rule_final is None:
            self.rule_final = self.final
        if self.base_final is None:
            if self.judge_final is None:
                self.base_final = self.rule_final
            else:
                self.base_final = round(self.rule_final * 0.60 + self.judge_final * 0.40, 2)
        return self


class EvaluationFeedbackRead(BaseModel):
    liked: bool = False
    like_count: int = Field(default=0, alias="likeCount")
    disliked: bool = False
    dislike_count: int = Field(default=0, alias="dislikeCount")


class ModelResponseRead(BaseModel):
    id: int
    model_config_id: int | None = Field(default=None, alias="modelConfigId")
    model_name: str = Field(alias="modelName")
    provider: str
    answer: str
    latency_ms: int = Field(alias="latencyMs")
    output_tokens: int = Field(alias="outputTokens")
    estimated_cost: float = Field(alias="estimatedCost")
    status: str
    score: EvaluationScoreRead
    feedback: EvaluationFeedbackRead = Field(default_factory=EvaluationFeedbackRead)


class EvaluationTaskRead(BaseModel):
    task_id: int = Field(alias="taskId")
    status: str
    prompt: str
    created_at: datetime | None = Field(default=None, alias="createdAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    responses: list[ModelResponseRead]


class EvaluationTaskListItemRead(BaseModel):
    task_id: int = Field(alias="taskId")
    status: str
    prompt: str
    created_at: datetime = Field(alias="createdAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    response_count: int = Field(alias="responseCount")


class EvaluationTaskListRead(BaseModel):
    items: list[EvaluationTaskListItemRead]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")


class FeedbackCreate(BaseModel):
    feedback_type: Literal["like", "dislike"] = Field(alias="feedbackType")


class FeedbackToggleRead(BaseModel):
    response_id: int = Field(alias="responseId")
    feedback_type: Literal["like", "dislike"] = Field(alias="feedbackType")
    active: bool
    feedback: EvaluationFeedbackRead
    score: EvaluationScoreRead


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)

    @field_validator("content", mode="before")
    @classmethod
    def strip_content(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CommentRead(BaseModel):
    id: int
    response_id: int = Field(alias="responseId")
    user_id: int = Field(alias="userId")
    username: str
    content: str
    created_at: datetime = Field(alias="createdAt")
    can_delete: bool = Field(alias="canDelete")


class CommentListRead(BaseModel):
    items: list[CommentRead]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
