from datetime import date

from fastapi.testclient import TestClient
import pytest

from app.api.dependencies import get_current_user, require_admin
from app.main import app
from app.models.user import User
from app.schemas.token_usage import AdminUserUsageRead, TokenUsageRead
from app.services.token_quota_service import TokenQuotaExceededError, token_quota_service


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


def test_list_admin_users_returns_usage_and_quota(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_list_users(_db: object) -> list[AdminUserUsageRead]:
        return [
            AdminUserUsageRead(
                id=7,
                username="test_user",
                role="user",
                status="active",
                usageDate=date(2026, 6, 12),
                usedTokens=24_000,
                dailyLimit=100_000,
            )
        ]

    monkeypatch.setattr(token_quota_service, "list_users", fake_list_users)

    response = TestClient(app).get("/api/admin/users")

    assert response.status_code == 200
    assert response.json()[0]["dailyLimit"] == 100_000


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
