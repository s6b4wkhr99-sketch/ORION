#!/usr/bin/env bash
# Start Ceragem CIOS locally: PostgreSQL + backend API + frontend UI
# Foreground mode — keep this terminal open (Ctrl+C stops both servers).
# For background servers that survive IDE/agent sessions: make dev-daemon
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
COMPOSE_FILE="$ROOT/docker-compose.postgres.yml"
PG_URL="${DATABASE_URL:-postgresql+psycopg2://cios:cios_dev_password@127.0.0.1:5432/cios}"

docker_cmd() {
  if command -v docker >/dev/null 2>&1; then
    docker "$@"
    return
  fi
  for candidate in /usr/local/bin/docker /opt/homebrew/bin/docker \
    /Applications/Docker.app/Contents/Resources/bin/docker; do
    if [ -x "$candidate" ]; then
      "$candidate" "$@"
      return
    fi
  done
  return 1
}

echo "==> Ceragem CIOS — local dev"
echo "    Frontend: http://localhost:3002"
echo "    Backend:  http://127.0.0.1:8000"
echo ""

free_port() {
  local port="$1"
  local pids
  pids=$(lsof -ti ":$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "==> Freeing port $port (stale process)…"
    kill $pids 2>/dev/null || true
    sleep 1
    kill -9 $pids 2>/dev/null || true
  fi
}

free_port 3002
free_port 8000

if docker_cmd info >/dev/null 2>&1; then
  echo "==> Starting PostgreSQL (Docker)…"
  docker_cmd compose -f "$COMPOSE_FILE" up -d
else
  echo "WARN: Docker not available — ensure PostgreSQL is running on 127.0.0.1:5432"
fi

echo "==> Waiting for PostgreSQL…"
PG_CHECK="$BACKEND/.venv/bin/python"
if [ ! -x "$PG_CHECK" ]; then
  PG_CHECK="python3"
fi
for _ in $(seq 1 30); do
  if PG_URL="$PG_URL" "$PG_CHECK" - <<'PY' 2>/dev/null
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
    break
  fi
  sleep 1
done

if [ ! -d "$BACKEND/.venv" ]; then
  echo "==> Creating Python venv…"
  python3 -m venv "$BACKEND/.venv"
  "$BACKEND/.venv/bin/pip" install -q -r "$BACKEND/requirements.txt"
fi

echo "==> Running migrations…"
(
  cd "$BACKEND"
  export DATABASE_URL="$PG_URL"
  . .venv/bin/activate
  alembic upgrade head
)

if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "==> Installing frontend dependencies…"
  (cd "$FRONTEND" && npm install)
fi

if [ ! -f "$FRONTEND/.env.local" ]; then
  cat > "$FRONTEND/.env.local" <<'EOF'
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SHOW_CAMPAIGN_MODULES=false
EOF
fi

cleanup() {
  echo ""
  echo "==> Shutting down local services…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "==> Starting backend (port 8000)…"
(
  cd "$BACKEND"
  export DATABASE_URL="$PG_URL"
  export SKIP_PHYSICAL_SCHEMA="${SKIP_PHYSICAL_SCHEMA:-true}"
  export DASHBOARD_CACHE_INVALIDATE_ON_STARTUP="${DASHBOARD_CACHE_INVALIDATE_ON_STARTUP:-false}"
  . .venv/bin/activate
  exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

echo "==> Starting frontend (port 3002)…"
(
  cd "$FRONTEND"
  exec npm run dev
) &
FRONTEND_PID=$!

echo ""
echo "Ready. Press Ctrl+C to stop both servers."
echo "  Market Intelligence: http://localhost:3002/market-intelligence"
echo ""

wait "$BACKEND_PID" "$FRONTEND_PID"
