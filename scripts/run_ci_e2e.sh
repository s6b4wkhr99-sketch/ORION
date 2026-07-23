#!/usr/bin/env bash
# Start backend + frontend for Playwright E2E (CI or local with PostgreSQL).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
LOG_DIR="$ROOT/.dev/logs/ci-e2e"
mkdir -p "$LOG_DIR"

DB_URL="${CI_DATABASE_URL:-${DATABASE_URL:-postgresql+psycopg2://cios:cios_ci_password@127.0.0.1:5432/cios}}"
export DATABASE_URL="$DB_URL"
export AUTH_REQUIRED=true
export SKIP_PHYSICAL_SCHEMA=true
export JWT_SECRET="${JWT_SECRET:-ci-e2e-test-secret}"
export CORS_ORIGINS="http://127.0.0.1:3002,http://localhost:3002"

PYTHON="python3"
if [ -x "$BACKEND/.venv/bin/python" ]; then
  PYTHON="$BACKEND/.venv/bin/python"
fi

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT

wait_http() {
  local url="$1"
  local label="$2"
  local max="${3:-60}"
  for i in $(seq 1 "$max"); do
    if curl -sf -o /dev/null -m 2 "$url" 2>/dev/null; then
      echo "✓ $label ready"
      return 0
    fi
    sleep 2
  done
  echo "ERROR: $label not ready at $url"
  return 1
}

echo "==> CI E2E stack setup"
echo "    DATABASE_URL=$DB_URL"

cd "$BACKEND"
"$PYTHON" -m pip install -q -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt
"$PYTHON" -m alembic upgrade head
"$PYTHON" scripts/init_postgres.py

echo "==> Starting backend on :8000"
"$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 \
  >"$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

wait_http "http://127.0.0.1:8000/api/v1/health" "Backend" 45

cd "$FRONTEND"
if [ ! -d node_modules ]; then
  npm ci
fi
if [ ! -d "$HOME/.cache/ms-playwright" ] && [ -z "${PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD:-}" ]; then
  npx playwright install chromium
fi

echo "==> Starting frontend on :3002"
BACKEND_URL=http://127.0.0.1:8000 npm run dev >"$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

wait_http "http://127.0.0.1:3002/login" "Frontend" 90

echo "==> Running Playwright E2E"
PLAYWRIGHT_BASE_URL=http://127.0.0.1:3002 npm run test:e2e

echo "✓ E2E tests passed"
