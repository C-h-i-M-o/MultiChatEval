from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "start-local.sh"


def test_start_local_runs_alembic_migrations_before_backend() -> None:
    script = SCRIPT_PATH.read_text()

    assert "run_migrations" in script
    assert ".venv/bin/alembic upgrade head" in script
    assert "run_migrations\n  start_backend" in script


def test_start_local_selects_available_ports_and_passes_backend_target_to_vite() -> None:
    script = SCRIPT_PATH.read_text()

    assert "find_available_port" in script
    assert 'BACKEND_PORT="$(find_available_port "${BACKEND_PORT}")"' in script
    assert 'FRONTEND_PORT="$(find_available_port "${FRONTEND_PORT}")"' in script
    assert 'VITE_BACKEND_TARGET="http://${BACKEND_HOST}:${BACKEND_PORT}"' in script
    assert 'warn "端口 ${port} 已被占用，尝试端口 $((port + 1))。" >&2' in script
    assert "--strictPort" in script


def test_start_local_does_not_download_embedding_model() -> None:
    script = SCRIPT_PATH.read_text()

    assert "sentence_transformers" not in script
    assert "prepare_embedding_model" not in script
    assert "SentenceTransformer" not in script
    assert "prepare_frontend\n  BACKEND_PORT" in script
