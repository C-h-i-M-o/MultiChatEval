from datetime import timedelta

import pytest

from app.core.security import (
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_can_be_verified_without_storing_plaintext() -> None:
    password_hash = hash_password("password123")

    assert password_hash != "password123"
    assert verify_password("password123", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_unknown_password_hash_is_rejected_without_error() -> None:
    assert verify_password("password123", "legacy-plain-value") is False


def test_access_token_round_trip_returns_user_id() -> None:
    token = create_access_token(42)

    assert decode_access_token(token) == 42


def test_expired_access_token_is_rejected() -> None:
    token = create_access_token(42, expires_delta=timedelta(seconds=-1))

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)
