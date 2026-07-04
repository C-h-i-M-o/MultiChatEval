from datetime import date

from fastapi.testclient import TestClient
import pytest

from app.api.dependencies import get_current_user, require_admin
from app.main import app
from app.models.user import User
from app.schemas.token_usage import AdminUserListRead, AdminUserUsageRead, TokenUsageRead
from app.services.token_quota_service import TokenQuotaExceededError, TokenQuotaUserError, token_quota_service


@pytest.fixture(autouse=True)
def authenticated_user() -> object:
    user = User(
        id=7,
        username="test_user",
        password_hash="unused",
        role="user",
        status="active",
    )
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: User(
        id=1,
        username="admin",
        password_hash="unused",
        role="admin",
        status="active",
    )
    yield
    app.dependency_overrides.clear()


def test_get_today_token_usage_returns_remaining_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get_today_usage(_db: object, user: User) -> TokenUsageRead:
        assert user.id == 7
        return TokenUsageRead(
            usageDate=date(2026, 6, 12),
            usedTokens=24_000,
            dailyLimit=100_000,
            remainingTokens=76_000,
            unlimited=False,
        )

    monkeypatch.setattr(token_quota_service, "get_today_usage", fake_get_today_usage)

    response = TestClient(app).get("/api/token-usage/me/today")

    assert response.status_code == 200
    assert response.json()["remainingTokens"] == 76_000


def test_list_admin_users_returns_paginated_usage_and_quota(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_list_users(
        _db: object,
        *,
        page: int,
        page_size: int,
        keyword: str | None,
        role: str | None,
        user_status: str | None,
    ) -> AdminUserListRead:
        assert page == 2
        assert page_size == 5
        assert keyword == "test"
        assert role == "user"
        assert user_status == "active"
        return AdminUserListRead(
            items=[
                AdminUserUsageRead(
                    id=7,
                    username="test_user",
                    role="user",
                    status="active",
                    usageDate=date(2026, 6, 12),
                    usedTokens=24_000,
                    dailyLimit=100_000,
                )
            ],
            total=6,
            page=2,
            pageSize=5,
        )

    monkeypatch.setattr(token_quota_service, "list_users", fake_list_users)

    response = TestClient(app).get(
        "/api/admin/users",
        params={
            "page": 2,
            "pageSize": 5,
            "keyword": "test",
            "role": "user",
            "status": "active",
        },
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["dailyLimit"] == 100_000
    assert response.json()["total"] == 6


def test_admin_can_disable_user(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_set_user_status(
        _db: object,
        *,
        user_id: int,
        user_status: str,
        operator_user_id: int,
    ) -> AdminUserUsageRead:
        assert user_id == 7
        assert user_status == "disabled"
        assert operator_user_id == 1
        return AdminUserUsageRead(
            id=7,
            username="test_user",
            role="user",
            status="disabled",
            usageDate=date(2026, 6, 12),
            usedTokens=24_000,
            dailyLimit=100_000,
        )

    monkeypatch.setattr(token_quota_service, "set_user_status", fake_set_user_status)

    response = TestClient(app).patch("/api/admin/users/7/status", json={"status": "disabled"})

    assert response.status_code == 200
    assert response.json()["status"] == "disabled"


def test_admin_cannot_disable_self(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_set_user_status(
        _db: object,
        *,
        user_id: int,
        user_status: str,
        operator_user_id: int,
    ) -> AdminUserUsageRead:
        raise TokenQuotaUserError("不能封禁当前登录的管理员账号")

    monkeypatch.setattr(token_quota_service, "set_user_status", fake_set_user_status)

    response = TestClient(app).patch("/api/admin/users/1/status", json={"status": "disabled"})

    assert response.status_code == 400
    assert response.json() == {"detail": "不能封禁当前登录的管理员账号"}


def test_quota_exceeded_error_uses_http_429(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_ensure_can_start(_db: object, _user: User) -> None:
        raise TokenQuotaExceededError("今日 Token 额度已用完")

    monkeypatch.setattr(token_quota_service, "ensure_can_start", fake_ensure_can_start)

    response = TestClient(app).post(
        "/api/evaluation/tasks",
        json={"prompt": "测试问题", "modelIds": [1]},
    )

    assert response.status_code == 429
    assert response.json() == {"detail": "今日 Token 额度已用完"}
