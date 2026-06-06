#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
LOG_DIR="${PROJECT_ROOT}/logs"
PYTHON_BIN="${PYTHON_BIN:-/opt/anaconda3/bin/python}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

BACKEND_PID=""
FRONTEND_PID=""

log() {
  printf "\033[1;34m[MultiChatEval]\033[0m %s\n" "$1"
}

warn() {
  printf "\033[1;33m[MultiChatEval]\033[0m %s\n" "$1"
}

fail() {
  printf "\033[1;31m[MultiChatEval]\033[0m %s\n" "$1" >&2
  exit 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

port_in_use() {
  local port="$1"
  lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1
}

find_available_port() {
  local port="$1"

  while port_in_use "${port}"; do
    warn "端口 ${port} 已被占用，尝试端口 $((port + 1))。" >&2
    port=$((port + 1))
  done

  printf "%s" "${port}"
}

cleanup() {
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
    log "停止后端服务..."
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi
  BACKEND_PID=""

  if [[ -n "${FRONTEND_PID}" ]] && kill -0 "${FRONTEND_PID}" >/dev/null 2>&1; then
    log "停止前端服务..."
    kill "${FRONTEND_PID}" >/dev/null 2>&1 || true
  fi
  FRONTEND_PID=""
}

require_command() {
  local command_name="$1"
  local install_hint="$2"

  if ! command_exists "${command_name}"; then
    fail "未找到 ${command_name}。${install_hint}"
  fi
}

wait_for_mysql() {
  local retries=30

  log "等待 MySQL 就绪..."
  while (( retries > 0 )); do
    if docker exec multichateval-mysql mysqladmin ping -h localhost >/dev/null 2>&1; then
      log "MySQL 已就绪。"
      return 0
    fi
    retries=$((retries - 1))
    sleep 2
  done

  fail "MySQL 在 60 秒内未就绪，请检查 Docker 或数据库日志。"
}

prepare_env_file() {
  if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
    log "未发现 .env，已从 .env.example 复制一份。"
    cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
  fi
}

prepare_backend() {
  local venv_python="${BACKEND_DIR}/.venv/bin/python"

  if [[ ! -x "${PYTHON_BIN}" ]]; then
    if command_exists python3; then
      warn "未找到 ${PYTHON_BIN}，改用系统 python3。"
      PYTHON_BIN="$(command -v python3)"
    else
      fail "未找到 Python。请安装 Python 3.11+，或设置 PYTHON_BIN=/path/to/python。"
    fi
  fi

  if [[ ! -x "${venv_python}" ]]; then
    log "创建后端虚拟环境..."
    "${PYTHON_BIN}" -m venv "${BACKEND_DIR}/.venv"
  fi

  log "校验并安装后端依赖..."
  (cd "${BACKEND_DIR}" && "${venv_python}" -m pip install -e ".[dev]")
}

prepare_frontend() {
  log "按锁文件校验并安装前端依赖..."
  (cd "${FRONTEND_DIR}" && pnpm install --frozen-lockfile)
}

run_migrations() {
  log "执行数据库迁移..."
  (cd "${BACKEND_DIR}" && .venv/bin/alembic upgrade head)
}

start_backend() {
  log "启动后端：http://${BACKEND_HOST}:${BACKEND_PORT}"
  (
    cd "${BACKEND_DIR}"
    .venv/bin/python -m uvicorn app.main:app --reload --host "${BACKEND_HOST}" --port "${BACKEND_PORT}"
  ) >"${LOG_DIR}/backend.log" 2>&1 &
  BACKEND_PID="$!"
}

start_frontend() {
  log "启动前端：http://${FRONTEND_HOST}:${FRONTEND_PORT}"
  (
    cd "${FRONTEND_DIR}"
    VITE_BACKEND_TARGET="http://${BACKEND_HOST}:${BACKEND_PORT}" pnpm dev --host "${FRONTEND_HOST}" --port "${FRONTEND_PORT}" --strictPort
  ) >"${LOG_DIR}/frontend.log" 2>&1 &
  FRONTEND_PID="$!"
}

wait_for_url() {
  local name="$1"
  local url="$2"
  local retries=30

  log "等待${name}就绪..."
  while (( retries > 0 )); do
    if curl --fail --silent --show-error "${url}" >/dev/null 2>&1; then
      log "${name}已就绪：${url}"
      return 0
    fi
    retries=$((retries - 1))
    sleep 1
  done

  fail "${name}在 30 秒内未就绪，请检查 ${LOG_DIR} 下的日志。"
}

watch_processes() {
  log "本地项目已启动。日志目录：${LOG_DIR}"
  log "按 Ctrl+C 停止后端和前端开发服务。"

  while true; do
    if ! kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
      warn "后端服务已退出，请查看 ${LOG_DIR}/backend.log。"
      exit 1
    fi

    if ! kill -0 "${FRONTEND_PID}" >/dev/null 2>&1; then
      warn "前端服务已退出，请查看 ${LOG_DIR}/frontend.log。"
      exit 1
    fi

    sleep 1
  done
}

main() {
  trap cleanup EXIT
  trap 'cleanup; exit 130' INT TERM

  require_command docker "请先安装 Docker Desktop 并启动 Docker。"
  require_command pnpm "请先安装 pnpm。"
  require_command lsof "请先安装 lsof。"
  require_command curl "请先安装 curl。"

  if ! docker compose version >/dev/null 2>&1; then
    fail "当前 Docker 未提供 Compose 插件，请安装或升级 Docker Desktop。"
  fi

  mkdir -p "${LOG_DIR}"
  prepare_env_file

  log "启动 MySQL 容器..."
  (cd "${PROJECT_ROOT}" && docker compose up -d mysql)
  wait_for_mysql

  prepare_backend
  prepare_frontend
  BACKEND_PORT="$(find_available_port "${BACKEND_PORT}")"
  FRONTEND_PORT="$(find_available_port "${FRONTEND_PORT}")"
  run_migrations
  start_backend
  wait_for_url "后端服务" "http://${BACKEND_HOST}:${BACKEND_PORT}/api/health"
  start_frontend
  wait_for_url "前端服务" "http://${FRONTEND_HOST}:${FRONTEND_PORT}"
  watch_processes
}

main "$@"
