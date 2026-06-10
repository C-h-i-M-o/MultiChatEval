import pytest

from app.scripts import create_admin as create_admin_script
from app.scripts.create_admin import parse_args


def test_create_admin_requires_username() -> None:
    with pytest.raises(SystemExit):
        parse_args([])


def test_create_admin_accepts_username() -> None:
    args = parse_args(["--username", "admin"])

    assert args.username == "admin"


@pytest.mark.asyncio
async def test_run_create_admin_disposes_engine_after_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def fake_create_admin(username: str, password: str) -> None:
        assert username == "admin"
        assert password == "password123"
        calls.append("create")

    async def fake_dispose() -> None:
        calls.append("dispose")

    class FakeEngine:
        dispose = staticmethod(fake_dispose)

    monkeypatch.setattr(create_admin_script, "create_admin", fake_create_admin)
    monkeypatch.setattr(create_admin_script, "engine", FakeEngine())

    await create_admin_script.run_create_admin("admin", "password123")

    assert calls == ["create", "dispose"]


@pytest.mark.asyncio
async def test_run_create_admin_disposes_engine_after_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def fake_create_admin(_username: str, _password: str) -> None:
        calls.append("create")
        raise ValueError("用户名已存在")

    async def fake_dispose() -> None:
        calls.append("dispose")

    class FakeEngine:
        dispose = staticmethod(fake_dispose)

    monkeypatch.setattr(create_admin_script, "create_admin", fake_create_admin)
    monkeypatch.setattr(create_admin_script, "engine", FakeEngine())

    with pytest.raises(ValueError, match="用户名已存在"):
        await create_admin_script.run_create_admin("admin", "password123")

    assert calls == ["create", "dispose"]
