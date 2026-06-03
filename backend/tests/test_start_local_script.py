from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "start-local.sh"


def test_start_local_runs_alembic_migrations_before_backend() -> None:
    script = SCRIPT_PATH.read_text()

    assert "run_migrations" in script
    assert ".venv/bin/alembic upgrade head" in script
    assert "run_migrations\n  start_backend" in script
