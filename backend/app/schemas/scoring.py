from typing import Literal

from pydantic import BaseModel, Field


class RuleDictionaryRead(BaseModel):
    id: int
    dictionary_type: str = Field(alias="dictionaryType")
    name: str
    version: str
    enabled: bool


class RuleTermRead(BaseModel):
    id: int
    dictionary_id: int = Field(alias="dictionaryId")
    dictionary_type: str = Field(alias="dictionaryType")
    category: str
    content: str
    match_type: Literal["keyword", "regex"] = Field(alias="matchType")
    severity: int
    enabled: bool
    updated_at: str = Field(alias="updatedAt")


class RuleTermListRead(BaseModel):
    items: list[RuleTermRead]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")


class RuleTermPayload(BaseModel):
    dictionary_id: int = Field(alias="dictionaryId")
    category: str
    content: str
    match_type: Literal["keyword", "regex"] = Field(alias="matchType")
    severity: int = Field(ge=1, le=10)
    enabled: bool = True


class RuleTermStatusPayload(BaseModel):
    enabled: bool


class JudgePromptGroupRead(BaseModel):
    id: int
    code: str
    name: str
    rubric: str
    version: str
    enabled: bool


class JudgePromptTemplateRead(BaseModel):
    id: int
    group_id: int = Field(alias="groupId")
    group_code: str = Field(alias="groupCode")
    code: str
    content: str
    output_schema: dict[str, object] = Field(alias="outputSchema")
    enabled: bool
    updated_at: str = Field(alias="updatedAt")


class JudgePromptTemplatePayload(BaseModel):
    content: str
    output_schema: dict[str, object] = Field(alias="outputSchema")
    enabled: bool


class JudgePromptValidationRead(BaseModel):
    valid: bool
    issues: list[str]
