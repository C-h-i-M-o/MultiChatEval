import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "clear-builtin-api-keys.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("clear_builtin_api_keys", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_clear_builtin_api_keys_targets_only_builtin_providers() -> None:
    module = load_script_module()

    assert module.BUILTIN_PROVIDER_NAMES == ("deepseek", "minimax", "glm")


def test_clear_builtin_api_keys_uses_sync_mysql_driver() -> None:
    module = load_script_module()

    assert module.sync_database_url().startswith("mysql+pymysql://")
