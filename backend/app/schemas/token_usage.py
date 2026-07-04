from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class TokenUsageRead(BaseModel):
    usage_date: date = Field(alias="usageDate")
    used_tokens: int = Field(alias="usedTokens")
    daily_limit: int | None = Field(alias="dailyLimit")
    remaining_tokens: int | None = Field(alias="remainingTokens")
    unlimited: bool


class AdminUserUsageRead(BaseModel):
    id: int
    username: str
    role: Literal["user", "admin"]
    status: Literal["active", "disabled"]
    usage_date: date = Field(alias="usageDate")
    used_tokens: int = Field(alias="usedTokens")
    daily_limit: int | None = Field(alias="dailyLimit")


class AdminUserListRead(BaseModel):
    items: list[AdminUserUsageRead]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")


class UserQuotaUpdate(BaseModel):
    daily_limit: int = Field(alias="dailyLimit", ge=0)


class UserStatusUpdate(BaseModel):
    status: Literal["active", "disabled"]
