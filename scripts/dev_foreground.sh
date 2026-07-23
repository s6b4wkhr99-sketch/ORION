#!/usr/bin/env bash
# Run CIOS dev servers in THIS terminal (stable on macOS — survives as long as the window stays open).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
LOG_DIR="$ROOT/.dev/logs"
PG_URL="${DATABASE_URL:-postgresql+psycopg2://cios:cios_dev_password@127.0.0.1:5432/cios}"

mkdir -p "$LOG_DIR"

echo "==> Stopping any detached dev servers..."
bash "$ROOT/scripts/dev_daemon.sh" stop 2>/dev/null || true

if ! PG_URL="$PG_URL" "$BACKEND/.venv/bin/python" - <<'PY' 2>/dev/null
import os, sys
import psycopg2
url = os.environ["PG_URL"].replace("postgresql+psycopg2://", "postgresql://")
psycopg2.connect(url).close()
PY
then
  echo "ERROR: PostgreSQL is not running at 127.0.0.1:5432"
  echo "Run: make postgres-up"
  exit 1
fi

cleanup() {
  echo ""
  echo "==> Stopping servers..."
  jobs -p | xargs kill 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "==> Starting backend on http://127.0.0.1:8000"
(
  cd "$BACKEND"
  export DATABASE_URL="$PG_URL"
  while true; do
    .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) backend exited; restarting in 2s" >> "$LOG_DIR/backend.log"
    sleep 2
  done
) >>"$LOG_DIR/backend.log" 2>&1 &

echo "==> Starting frontend on http://127.0.0.1:3002"
(
  cd "$FRONTEND"
  while true; do
    ./node_modules/.bin/next dev --webpack -p 3002 -H 127.0.0.1
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) frontend exited; restarting in 2s" >> "$LOG_DIR/frontend.log"
    sleep 2
  done
) >>"$LOG_DIR/frontend.log" 2>&1 &

echo "==> Waiting for servers..."
ready=0
for _ in $(seq 1 90); do
  if curl -sf -o /dev/null -m 2 http://127.0.0.1:8000/api/v1/health 2>/dev/null \
    && curl -sf -o /dev/null -m 2 http://127.0.0.1:3002/login 2>/dev/null; then
    ready=1
    break
  fi
  sleep 1
done

if [ "$ready" != 1 ]; then
  echo "ERROR: Servers did not become ready. Check $LOG_DIR/"
  tail -n 15 "$LOG_DIR/backend.log" 2>/dev/null || true
  tail -n 15 "$LOG_DIR/frontend.log" 2>/dev/null || true
  exit 1
fi

echo ""
echo "✓ CIOS is running"
echo "  Login:    http://127.0.0.1:3002/login"
echo "  Admin:    http://127.0.0.1:3002/admin/users"
echo "  Backend:  http://127.0.0.1:8000/api/v1/health"
echo ""
echo "Default login: user@company.com / Ceragem2026!Adm"
echo ""
echo "IMPORTANT: Keep this Terminal window open while you work."
echo "Press Ctrl+C here to stop both servers."
echo ""

open "http://127.0.0.1:3002/login" 2>/dev/null || true

wait
