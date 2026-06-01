from pathlib import Path
import sys

from sqlalchemy import bindparam, create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings


BUILTIN_PROVIDER_NAMES = ("deepseek", "minimax", "glm")


def sync_database_url() -> str:
    return settings.database_url.replace("+aiomysql", "+pymysql", 1)


def main() -> None:
    engine = create_engine(sync_database_url(), pool_pre_ping=True)
    with engine.begin() as connection:
        result = connection.execute(
            text(
                """
                UPDATE model_providers
                SET api_key_encrypted = NULL
                WHERE name IN :provider_names
                """
            ).bindparams(bindparam("provider_names", expanding=True)),
            {"provider_names": BUILTIN_PROVIDER_NAMES},
        )
    print(f"已清空 {result.rowcount} 条内置模型供应商 API Key。")


if __name__ == "__main__":
    main()
