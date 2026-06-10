from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AuthCredentials(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if username.casefold() == "anonymous":
            raise ValueError("用户名不可使用系统保留名称")
        if any(character.isspace() or not character.isprintable() for character in username):
            raise ValueError("用户名不能包含空白或控制字符")
        return username


class UserRead(BaseModel):
    id: int
    username: str
    role: Literal["user", "admin"]
    status: Literal["active", "disabled"]
