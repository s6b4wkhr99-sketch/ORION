#!/usr/bin/env bash
# Shared helpers for scripts/dev.sh and local dev tooling.
set -euo pipefail

DEV_COMMON_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="${DEV_COMMON_ROOT}/backend"
FRONTEND="${DEV_COMMON_ROOT}/frontend"
LOG_DIR="${DEV_COMMON_ROOT}/.dev/logs"
PG_URL="${DATABASE_URL:-postgresql+psycopg2://cios:cios_dev_password@127.0.0.1:5432/cios}"

read_app_version() {
  if [ -f "${DEV_COMMON_ROOT}/VERSION" ]; then
    tr -d '[:space:]' < "${DEV_COMMON_ROOT}/VERSION"
  else
    echo "unknown"
  fi
}

read_backend_env() {
  local key="$1"
  local default="${2:-}"
  local file="${BACKEND}/.env"
  if [ ! -f "$file" ]; then
    echo "$default"
    return
  fi
  local line
  line="$(grep -E "^${key}=" "$file" | tail -1 || true)"
  if [ -z "$line" ]; then
    echo "$default"
    return
  fi
  echo "${line#*=}" | tr -d '"' | tr -d "'"
}

port_listening() {
  lsof -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null | head -1 || true
}

health_backend() {
  curl -sf -o /dev/null -m 3 http://127.0.0.1:8000/api/v1/health 2>/dev/null
}

health_frontend() {
  curl -sf -o /dev/null -m 3 http://127.0.0.1:3002/login 2>/dev/null
}

backend_version_live() {
  curl -sf -m 3 http://127.0.0.1:8000/api/v1/health 2>/dev/null \
    | "${BACKEND}/.venv/bin/python" -c "import json,sys; d=json.load(sys.stdin); print(d.get('data',{}).get('version','?'))" 2>/dev/null \
    || echo "?"
}

openapi_has_delete_user() {
  curl -sf -m 5 http://127.0.0.1:8000/openapi.json 2>/dev/null \
    | "${BACKEND}/.venv/bin/python" -c "import json,sys; d=json.load(sys.stdin); print('yes' if 'delete' in d.get('paths',{}).get('/api/v1/admin/users/{email}',{}) else 'no')" 2>/dev/null \
    || echo "no"
}

check_postgres() {
  local py="${BACKEND}/.venv/bin/python"
  [ -x "$py" ] || py="python3"
  PG_URL="$PG_URL" "$py" - <<'PY' 2>/dev/null
import os, sys
try:
    import psycopg2
    url = os.environ.get("PG_URL", "").replace("postgresql+psycopg2://", "postgresql://")
    psycopg2.connect(url).close()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
}

worker_running() {
  pgrep -f "python -m app.worker.main" >/dev/null 2>&1 \
    || pgrep -f "app.worker.main" >/dev/null 2>&1
}

start_worker_background() {
  mkdir -p "$LOG_DIR"
  if worker_running; then
    echo "==> Upload worker already running"
    return 0
  fi
  if [ ! -x "${BACKEND}/.venv/bin/python" ]; then
    echo "ERROR: Backend venv missing. Run: bash scripts/setup_local.sh"
    return 1
  fi
  echo "==> Starting upload worker in background (logs: $LOG_DIR/worker.log)"
  (
    cd "$BACKEND"
    source .venv/bin/activate
    export WORKER_POLL_SECONDS="${WORKER_POLL_SECONDS:-5}"
    export DATABASE_URL="$PG_URL"
    exec python -m app.worker.main
  ) >>"$LOG_DIR/worker.log" 2>&1 &
  disown 2>/dev/null || true
  sleep 1
  worker_running && echo "    Worker OK" || echo "    Worker may still be starting — check $LOG_DIR/worker.log"
}

stop_worker() {
  pkill -f "python -m app.worker.main" 2>/dev/null || true
  pkill -f "app.worker.main" 2>/dev/null || true
}

stop_all_servers() {
  bash "${DEV_COMMON_ROOT}/scripts/dev_daemon.sh" stop 2>/dev/null || true
  for port in 8000 3002; do
    local pids
    pids="$(lsof -ti ":$port" 2>/dev/null || true)"
    if [ -n "$pids" ]; then
      echo "==> Freeing port $port..."
      kill $pids 2>/dev/null || true
      sleep 0.5
      kill -9 $pids 2>/dev/null || true
    fi
  done
  pkill -f "next dev --webpack -p 3002" 2>/dev/null || true
  pkill -f "uvicorn app.main:app --host 127.0.0.1 --port 8000" 2>/dev/null || true
}

warn_upload_worker() {
  local async_flag async_lower
  async_flag="$(read_backend_env UPLOAD_ASYNC false)"
  async_lower="$(printf '%s' "$async_flag" | tr '[:upper:]' '[:lower:]')"
  case "$async_lower" in
    true|1|yes)
      if worker_running; then
        echo "✓ Upload worker running (UPLOAD_ASYNC=true)"
      else
        echo ""
        echo "⚠ UPLOAD_ASYNC=true but upload worker is not running."
        echo "  Large uploads will stay queued. Fix:"
        echo "    make worker"
        echo "  Or start with worker:"
        echo "    bash scripts/dev.sh start --with-worker"
        echo ""
      fi
      ;;
  esac
}
