#!/usr/bin/env bash
# Run Ceragem CIOS backend + frontend detached from the shell (survives Cursor/agent terminals).
# Usage: bash scripts/dev_daemon.sh {start|stop|restart|status|logs}
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
DEV_DIR="$ROOT/.dev"
LOG_DIR="$DEV_DIR/logs"
BACKEND_PID_FILE="$DEV_DIR/backend.pid"
FRONTEND_PID_FILE="$DEV_DIR/frontend.pid"
PG_URL="${DATABASE_URL:-postgresql+psycopg2://cios:cios_dev_password@127.0.0.1:5432/cios}"

mkdir -p "$LOG_DIR"

launch_detached() {
  local logfile="$1"
  shift
  if command -v setsid >/dev/null 2>&1; then
    setsid nohup "$@" >>"$logfile" 2>&1 </dev/null &
  else
    nohup "$@" >>"$logfile" 2>&1 </dev/null &
  fi
  local pid=$!
  disown -h "$pid" 2>/dev/null || true
  echo "$pid"
}

port_pids() {
  lsof -ti ":$1" 2>/dev/null || true
}

port_listening() {
  lsof -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null | head -1 || true
}

is_running() {
  local pid="$1"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

read_pid_file() {
  local file="$1"
  if [ -f "$file" ]; then
    cat "$file"
  fi
}

health_backend() {
  curl -sf -o /dev/null -m 2 http://127.0.0.1:8000/api/v1/health 2>/dev/null
}

health_frontend() {
  local code
  for url in "http://127.0.0.1:3002/" "http://localhost:3002/"; do
    code=$(curl -s -o /dev/null -m 2 -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    [ "$code" != "000" ] && [ -n "$code" ] && return 0
  done
  return 1
}

stop_service() {
  local name="$1"
  local pid_file="$2"
  local port="$3"
  local pid
  pid="$(read_pid_file "$pid_file")"

  if is_running "$pid"; then
    echo "==> Stopping $name (pid $pid)..."
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 10); do
      is_running "$pid" || break
      sleep 0.5
    done
    if is_running "$pid"; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi

  local stale
  stale="$(port_pids "$port")"
  if [ -n "$stale" ]; then
    echo "==> Freeing port $port..."
    kill $stale 2>/dev/null || true
    sleep 0.5
    kill -9 $stale 2>/dev/null || true
  fi

  rm -f "$pid_file"
}

stop_all_dev() {
  stop_service "frontend" "$FRONTEND_PID_FILE" 3002
  stop_service "backend" "$BACKEND_PID_FILE" 8000
  pkill -f "next dev --webpack -p 3002" 2>/dev/null || true
  pkill -f "next start -p 3002" 2>/dev/null || true
  pkill -f "uvicorn app.main:app --host 127.0.0.1 --port 8000" 2>/dev/null || true
}

ensure_postgres() {
  local py="$BACKEND/.venv/bin/python"
  if [ ! -x "$py" ]; then
    py="python3"
  fi
  if PG_URL="$PG_URL" "$py" - <<'PY' 2>/dev/null
import os, sys
try:
    import psycopg2
    url = os.environ.get("PG_URL", "").replace("postgresql+psycopg2://", "postgresql://")
    conn = psycopg2.connect(url)
    conn.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
  then
    return 0
  fi
  echo "ERROR: PostgreSQL is not reachable at 127.0.0.1:5432"
  echo "       Run: make postgres-up   (or start Docker Postgres manually)"
  return 1
}

ensure_backend_venv() {
  if [ ! -d "$BACKEND/.venv" ]; then
    echo "==> Creating Python venv..."
    python3 -m venv "$BACKEND/.venv"
    "$BACKEND/.venv/bin/pip" install -q -r "$BACKEND/requirements.txt"
  fi
}

ensure_frontend_env() {
  if [ ! -f "$FRONTEND/.env.local" ]; then
    cat > "$FRONTEND/.env.local" <<'EOF'
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SHOW_CAMPAIGN_MODULES=false
NEXT_PUBLIC_AUTH_REQUIRED=true
EOF
  fi
  if [ ! -d "$FRONTEND/node_modules" ]; then
    echo "==> Installing frontend dependencies..."
    (cd "$FRONTEND" && npm install)
  fi
}

start_backend() {
  local pid
  pid="$(read_pid_file "$BACKEND_PID_FILE")"
  if [ -n "$pid" ] && ! is_running "$pid"; then
    rm -f "$BACKEND_PID_FILE"
    pid=""
  fi
  if is_running "$pid" && health_backend; then
    echo "==> Backend already running (pid $pid)"
    return 0
  fi
  stop_service "backend" "$BACKEND_PID_FILE" 8000
  ensure_backend_venv

  echo "==> Starting backend (port 8000)..."
  cd "$BACKEND"
  export DATABASE_URL="$PG_URL"
  # Restart loop keeps port 8000 alive after rescore/long jobs that stop uvicorn.
  pid="$(
    launch_detached "$LOG_DIR/backend.log" bash -c '
      while true; do
        .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) backend exited; restarting in 2s" >> "'"$LOG_DIR/backend.log"'"
        sleep 2
      done
    '
  )"
  cd "$ROOT"
  echo "$pid" >"$BACKEND_PID_FILE"

  echo "    Waiting for backend (cache warm may take ~60s)..."
  for _ in $(seq 1 180); do
    health_backend && break
    sleep 1
  done
  if ! health_backend; then
    echo "ERROR: Backend failed to start. See $LOG_DIR/backend.log"
    tail -n 20 "$LOG_DIR/backend.log" 2>/dev/null || true
    return 1
  fi
  echo "    Backend OK — http://127.0.0.1:8000"
}

start_frontend() {
  local pid
  pid="$(read_pid_file "$FRONTEND_PID_FILE")"
  if [ -n "$pid" ] && ! is_running "$pid"; then
    rm -f "$FRONTEND_PID_FILE"
    pid=""
  fi
  if is_running "$pid" && health_frontend; then
    echo "==> Frontend already running (pid $pid)"
    return 0
  fi
  stop_service "frontend" "$FRONTEND_PID_FILE" 3002
  ensure_frontend_env

  local frontend_mode="${CIOS_FRONTEND_MODE:-dev}"
  echo "==> Starting frontend (port 3002, mode=$frontend_mode)..."

  if [ "$frontend_mode" = "dev" ]; then
    pid="$(
      launch_detached "$LOG_DIR/frontend.log" bash -c '
        while true; do
          cd "'"$FRONTEND"'" && ./node_modules/.bin/next dev --webpack -p 3002 -H 127.0.0.1
          echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) frontend exited; restarting in 2s" >> "'"$LOG_DIR/frontend.log"'"
          sleep 2
        done
      '
    )"
  else
    pid="$(
      launch_detached "$LOG_DIR/frontend.log" bash -c '
        cd "'"$FRONTEND"'"
        if [ ! -f .next/BUILD_ID ]; then
          echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) building frontend (first run, ~2-4 min)..." >> "'"$LOG_DIR/frontend.log"'"
          ./node_modules/.bin/next build >> "'"$LOG_DIR/frontend.log"'" 2>&1 || exit 1
        fi
        mkdir -p .next/standalone/frontend/.next
        cp -R public .next/standalone/frontend/public 2>/dev/null || true
        cp -R .next/static .next/standalone/frontend/.next/static 2>/dev/null || true
        while true; do
          cd .next/standalone/frontend && PORT=3002 HOSTNAME=:: node server.js
          echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) frontend exited; restarting in 2s" >> "'"$LOG_DIR/frontend.log"'"
          sleep 2
        done
      '
    )"
  fi
  echo "$pid" >"$FRONTEND_PID_FILE"

  if [ "$frontend_mode" = "stable" ] && [ ! -f "$FRONTEND/.next/BUILD_ID" ]; then
    echo "    Building frontend (first run — may take 2-4 min). Tail: $LOG_DIR/frontend.log"
    for _ in $(seq 1 300); do
      health_frontend && break
      sleep 2
    done
  else
    for _ in $(seq 1 90); do
      health_frontend && break
      sleep 1
    done
  fi
  if ! health_frontend; then
    echo "ERROR: Frontend failed to start. See $LOG_DIR/frontend.log"
    tail -n 20 "$LOG_DIR/frontend.log" 2>/dev/null || true
    return 1
  fi
  echo "    Frontend OK — http://127.0.0.1:3002/mission-control"
}

cmd_start() {
  echo "==> Ceragem CIOS — detached dev servers"
  ensure_postgres
  ensure_backend_venv
  echo "==> Invalidating dashboard cache (promo/coverage policy changes)..."
  (
    cd "$BACKEND"
    export DATABASE_URL="$PG_URL"
    PYTHONPATH=. .venv/bin/python -c "from app.cache.dashboard_cache import invalidate_dashboard_cache; invalidate_dashboard_cache()"
  ) || echo "    (cache invalidate skipped — backend venv not ready)"
  start_backend
  start_frontend
  echo ""
  echo "Servers run in the background. Logs: $LOG_DIR/"
  echo "Stop with: make dev-stop"
}

cmd_stop() {
  echo "==> Stopping Ceragem CIOS dev servers..."
  stop_all_dev
  echo "Done."
}

cmd_status() {
  local bp fp bl fl
  bp="$(read_pid_file "$BACKEND_PID_FILE")"
  fp="$(read_pid_file "$FRONTEND_PID_FILE")"
  bl="$(port_listening 8000)"
  fl="$(port_listening 3002)"

  echo "Ceragem CIOS dev status"
  echo "  Backend  supervisor=${bp:-—}  listener=${bl:-—}  health=$(health_backend && echo up || echo down)"
  echo "  Frontend supervisor=${fp:-—}  listener=${fl:-—}  health=$(health_frontend && echo up || echo down)"
  if [ -z "$bl" ] || [ -z "$fl" ]; then
    echo ""
    echo "  One or more servers are down. Run: make dev-restart"
    echo "  Or double-click: Start CIOS.command (keep Terminal open)"
  fi
  echo "  Logs: $LOG_DIR/"
}

cmd_logs() {
  local target="${1:-all}"
  case "$target" in
    backend) tail -n 40 -f "$LOG_DIR/backend.log" ;;
    frontend) tail -n 40 -f "$LOG_DIR/frontend.log" ;;
    all|*)
      echo "=== backend.log (last 20) ==="
      tail -n 20 "$LOG_DIR/backend.log" 2>/dev/null || echo "(empty)"
      echo ""
      echo "=== frontend.log (last 20) ==="
      tail -n 20 "$LOG_DIR/frontend.log" 2>/dev/null || echo "(empty)"
      ;;
  esac
}

ACTION="${1:-start}"
case "$ACTION" in
  start) cmd_start ;;
  stop) cmd_stop ;;
  restart) cmd_stop; cmd_start ;;
  status) cmd_status ;;
  logs) cmd_logs "${2:-all}" ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs [backend|frontend]}"
    exit 1
    ;;
esac
