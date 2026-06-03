from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EvaluationTaskCreate(BaseModel):
    conversation_id: int | None = Field(default=None, alias="conversationId")
    prompt: str
    model_ids: list[int] = Field(default_factory=list, alias="modelIds")
    enable_judge: bool = Field(default=False, alias="enableJudge")
    enable_thinking: bool = Field(default=False, alias="enableThinking")


class EvaluationScoreRead(BaseModel):
    relevance: float
    completeness: float
    clarity: float
    format: float
    safety: float
    final: float
    details: dict[str, list[str]] = Field(default_factory=dict)


class EvaluationFeedbackRead(BaseModel):
    liked: bool = False
    accepted: bool = False
    like_count: int = Field(default=0, alias="likeCount")
    accepted_count: int = Field(default=0, alias="acceptedCount")


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
    feedback_type: Literal["like", "accepted"] = Field(alias="feedbackType")
    comment: str | None = None


class FeedbackToggleRead(BaseModel):
    response_id: int = Field(alias="responseId")
    feedback_type: Literal["like", "accepted"] = Field(alias="feedbackType")
    active: bool
    feedback: EvaluationFeedbackRead
