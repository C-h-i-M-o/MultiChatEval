#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CI="${CI:-true}"

PNPM_BIN="${PNPM_BIN:-pnpm}"
if [ -x "/opt/homebrew/bin/pnpm" ]; then
  PNPM_BIN="/opt/homebrew/bin/pnpm"
fi

log() {
  printf "\033[1;34m[React Rewrite Verify]\033[0m %s\n" "$1"
}

run_in() {
  local dir="$1"
  shift
  log "运行：cd ${dir#"$ROOT_DIR"/} && $*"
  (cd "$dir" && "$@")
}

if [ ! -x "$ROOT_DIR/backend/.venv/bin/pytest" ]; then
  printf "后端虚拟环境不存在或未安装 pytest，请先运行 ./scripts/start-react-local.sh 或手动准备 backend/.venv。\n" >&2
  exit 1
fi

log "开始 React 重构并行验收。"
run_in "$ROOT_DIR/backend" .venv/bin/pytest -q
run_in "$ROOT_DIR/frontend" "$PNPM_BIN" test
run_in "$ROOT_DIR/frontend" "$PNPM_BIN" build
run_in "$ROOT_DIR/vue-frontend" "$PNPM_BIN" test
run_in "$ROOT_DIR/vue-frontend" "$PNPM_BIN" build
run_in "$ROOT_DIR" git diff --check
log "React 重构并行验收完成。"
