from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserRead


class DuplicateUsernameError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class UserDisabledError(Exception):
    pass


class AuthService:
    async def register(self, db: AsyncSession, username: str, password: str) -> UserRead:
        existing = await self.get_user_by_username(db, username)
        if existing is not None:
            raise DuplicateUsernameError("用户名已存在")

        user = User(
            username=username,
            password_hash=hash_password(password),
            role="user",
            status="active",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return self.serialize_user(user)

    async def authenticate(self, db: AsyncSession, username: str, password: str) -> UserRead:
        user = await self.get_user_by_username(db, username)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("用户名或密码错误")
        if user.status != "active":
            raise UserDisabledError("用户已被禁用")

        user.last_login_at = datetime.utcnow()
        await db.commit()
        return self.serialize_user(user)

    async def get_user_by_username(self, db: AsyncSession, username: str) -> User | None:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    def serialize_user(self, user: User) -> UserRead:
        return UserRead(
            id=user.id,
            username=user.username,
            role=user.role,
            status=user.status,
        )


auth_service = AuthService()
