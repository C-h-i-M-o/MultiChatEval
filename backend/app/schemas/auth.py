from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


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


class RegisterCredentials(AuthCredentials):
    confirm_password: str = Field(alias="confirmPassword", min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        has_digit = any(character.isdigit() for character in value)
        has_lower = any(character.islower() for character in value)
        has_upper = any(character.isupper() for character in value)
        if not (has_digit and has_lower and has_upper):
            raise ValueError("密码必须包含数字、小写字母和大写字母")
        return value

    @model_validator(mode="after")
    def validate_confirm_password(self) -> "RegisterCredentials":
        if self.password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        return self


class UserRead(BaseModel):
    id: int
    username: str
    role: Literal["user", "admin"]
    status: Literal["active", "disabled"]
