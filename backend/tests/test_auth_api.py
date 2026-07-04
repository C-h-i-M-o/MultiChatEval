from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import UserRead
from app.schemas.model_config import ModelConfigRead
from app.services.auth_service import DuplicateUsernameError, InvalidCredentialsError, auth_service
from app.services.model_config_service import model_config_service


def test_register_sets_auth_cookie(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_register(_db: object, username: str, password: str) -> UserRead:
        assert username == "demo_user"
        assert password == "Password123"
        return UserRead(id=1, username=username, role="user", status="active")

    monkeypatch.setattr(auth_service, "register", fake_register)

    response = TestClient(app).post(
        "/api/auth/register",
        json={"username": "demo_user", "password": "Password123", "confirmPassword": "Password123"},
    )

    assert response.status_code == 201
    assert response.json()["username"] == "demo_user"
    assert "multichateval_access_token=" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]


def test_register_returns_409_for_duplicate_username(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_register(_db: object, _username: str, _password: str) -> None:
        raise DuplicateUsernameError("用户名已存在")

    monkeypatch.setattr(auth_service, "register", fake_register)

    response = TestClient(app).post(
        "/api/auth/register",
        json={"username": "demo_user", "password": "Password123", "confirmPassword": "Password123"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "用户名已存在"}


def test_register_rejects_mismatched_confirm_password() -> None:
    response = TestClient(app).post(
        "/api/auth/register",
        json={"username": "demo_user", "password": "Password123", "confirmPassword": "Password124"},
    )

    assert response.status_code == 422
    assert "两次输入的密码不一致" in response.text


def test_register_requires_strong_password() -> None:
    response = TestClient(app).post(
        "/api/auth/register",
        json={"username": "demo_user", "password": "password123", "confirmPassword": "password123"},
    )

    assert response.status_code == 422
    assert "密码必须包含数字、小写字母和大写字母" in response.text


def test_login_rejects_invalid_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_authenticate(_db: object, _username: str, _password: str) -> None:
        raise InvalidCredentialsError("用户名或密码错误")

    monkeypatch.setattr(auth_service, "authenticate", fake_authenticate)

    response = TestClient(app).post(
        "/api/auth/login",
        json={"username": "demo_user", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "用户名或密码错误"}


def test_logout_clears_auth_cookie() -> None:
    response = TestClient(app).post("/api/auth/logout")

    assert response.status_code == 204
    assert "multichateval_access_token=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_me_returns_current_user() -> None:
    app.dependency_overrides[get_current_user] = lambda: User(
        id=7,
        username="demo_user",
        password_hash="unused",
        role="user",
        status="active",
    )
    try:
        response = TestClient(app).get("/api/auth/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "id": 7,
        "username": "demo_user",
        "role": "user",
        "status": "active",
    }


def test_protected_evaluation_endpoint_requires_login() -> None:
    response = TestClient(app).get("/api/evaluation/tasks")

    assert response.status_code == 401


def test_regular_user_cannot_access_admin_model_configs() -> None:
    app.dependency_overrides[get_current_user] = lambda: User(
        id=7,
        username="demo_user",
        password_hash="unused",
        role="user",
        status="active",
    )
    try:
        response = TestClient(app).get("/api/admin/model-configs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_admin_can_access_model_configs(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_list_configs(_db: object) -> list[ModelConfigRead]:
        return []

    monkeypatch.setattr(model_config_service, "list_configs", fake_list_configs)
    app.dependency_overrides[get_current_user] = lambda: User(
        id=8,
        username="admin_user",
        password_hash="unused",
        role="admin",
        status="active",
    )
    try:
        response = TestClient(app).get("/api/admin/model-configs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []
