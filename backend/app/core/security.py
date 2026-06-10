from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.core.config import settings

password_hash = PasswordHash.recommended()
AUTH_COOKIE_NAME = "multichateval_access_token"


class InvalidAccessTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        return password_hash.verify(password, encoded_hash)
    except UnknownHashError:
        return False


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": expires_at,
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        subject = payload.get("sub")
        if subject is None:
            raise InvalidAccessTokenError("登录凭据无效")
        return int(subject)
    except (InvalidTokenError, TypeError, ValueError) as error:
        raise InvalidAccessTokenError("登录凭据无效或已过期") from error
