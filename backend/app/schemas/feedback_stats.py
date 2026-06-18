from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


FeedbackStatsRange = Literal["7d", "30d", "all"]
FeedbackActivityType = Literal["all", "like", "dislike", "comment"]


class FeedbackStatsSummary(BaseModel):
    task_count: int = Field(default=0, alias="taskCount")
    call_count: int = Field(default=0, alias="callCount")
    scored_count: int = Field(default=0, alias="scoredCount")
    average_final_score: float | None = Field(default=None, alias="averageFinalScore")
    like_count: int = Field(default=0, alias="likeCount")
    dislike_count: int = Field(default=0, alias="dislikeCount")
    like_rate: float | None = Field(default=None, alias="likeRate")
    comment_count: int = Field(default=0, alias="commentCount")


class FeedbackInteractionSummary(BaseModel):
    like_count: int = Field(default=0, alias="likeCount")
    dislike_count: int = Field(default=0, alias="dislikeCount")
    comment_count: int = Field(default=0, alias="commentCount")


class FeedbackModelStats(BaseModel):
    model_config_id: int | None = Field(default=None, alias="modelConfigId")
    model_name: str = Field(alias="modelName")
    call_count: int = Field(default=0, alias="callCount")
    scored_count: int = Field(default=0, alias="scoredCount")
    average_final_score: float | None = Field(default=None, alias="averageFinalScore")
    average_rule_score: float | None = Field(default=None, alias="averageRuleScore")
    average_judge_score: float | None = Field(default=None, alias="averageJudgeScore")
    like_count: int = Field(default=0, alias="likeCount")
    dislike_count: int = Field(default=0, alias="dislikeCount")
    like_rate: float | None = Field(default=None, alias="likeRate")
    comment_count: int = Field(default=0, alias="commentCount")


class FeedbackTrendPoint(BaseModel):
    date: date
    call_count: int = Field(default=0, alias="callCount")
    average_final_score: float | None = Field(default=None, alias="averageFinalScore")
    like_count: int = Field(default=0, alias="likeCount")
    dislike_count: int = Field(default=0, alias="dislikeCount")
    comment_count: int = Field(default=0, alias="commentCount")


class FeedbackActivityRead(BaseModel):
    activity_id: int = Field(alias="activityId")
    activity_type: Literal["like", "dislike", "comment"] = Field(alias="activityType")
    user_id: int = Field(alias="userId")
    username: str
    task_id: int = Field(alias="taskId")
    response_id: int = Field(alias="responseId")
    model_config_id: int | None = Field(default=None, alias="modelConfigId")
    model_name: str = Field(alias="modelName")
    prompt: str
    content: str | None = None
    created_at: datetime = Field(alias="createdAt")


class FeedbackActivityListRead(BaseModel):
    items: list[FeedbackActivityRead] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = Field(default=20, alias="pageSize")


class PersonalFeedbackStatsRead(BaseModel):
    scope: Literal["personal"] = "personal"
    range: FeedbackStatsRange
    start_at: datetime | None = Field(default=None, alias="startAt")
    end_at: datetime = Field(alias="endAt")
    summary: FeedbackStatsSummary = Field(default_factory=FeedbackStatsSummary)
    my_interactions: FeedbackInteractionSummary = Field(
        default_factory=FeedbackInteractionSummary,
        alias="myInteractions",
    )
    models: list[FeedbackModelStats] = Field(default_factory=list)
    trend: list[FeedbackTrendPoint] = Field(default_factory=list)


class AdminFeedbackStatsRead(BaseModel):
    scope: Literal["global"] = "global"
    range: FeedbackStatsRange
    start_at: datetime | None = Field(default=None, alias="startAt")
    end_at: datetime = Field(alias="endAt")
    summary: FeedbackStatsSummary = Field(default_factory=FeedbackStatsSummary)
    models: list[FeedbackModelStats] = Field(default_factory=list)
    trend: list[FeedbackTrendPoint] = Field(default_factory=list)
    activities: FeedbackActivityListRead = Field(default_factory=FeedbackActivityListRead)
