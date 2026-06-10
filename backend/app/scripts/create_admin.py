import argparse
import asyncio
from getpass import getpass

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal, engine
from app.models.user import User
from app.services.auth_service import auth_service


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="创建 MultiChatEval 管理员")
    parser.add_argument("--username", required=True, help="管理员用户名")
    return parser.parse_args(argv)


async def create_admin(username: str, password: str) -> None:
    async with AsyncSessionLocal() as db:
        existing = await auth_service.get_user_by_username(db, username)
        if existing is not None:
            raise ValueError("用户名已存在，请使用其他用户名")

        db.add(
            User(
                username=username,
                password_hash=hash_password(password),
                role="admin",
                status="active",
            )
        )
        await db.commit()


async def run_create_admin(username: str, password: str) -> None:
    try:
        await create_admin(username, password)
    finally:
        await engine.dispose()


def main() -> None:
    args = parse_args()
    password = getpass("管理员密码：")
    confirmation = getpass("再次输入密码：")
    if password != confirmation:
        raise SystemExit("两次输入的密码不一致")
    if len(password) < 8:
        raise SystemExit("密码长度不能少于 8 个字符")
    asyncio.run(run_create_admin(args.username, password))
    print(f"管理员 {args.username} 创建成功")


if __name__ == "__main__":
    main()
