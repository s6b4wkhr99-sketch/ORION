#!/usr/bin/env bash
# Capture all ORION menu screenshots (requires local stack).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Checking dev servers..."
if curl -sf -o /dev/null http://127.0.0.1:3002/login && curl -sf -o /dev/null http://127.0.0.1:8000/api/v1/health; then
  echo "    Servers already up — skipping restart"
else
  echo "==> Starting dev servers..."
  bash scripts/dev_daemon.sh restart
fi

echo "==> Waiting for frontend..."
for i in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3002/login 2>/dev/null || echo "000")
  if [ "$code" = "200" ]; then
    echo "    Frontend ready (HTTP $code)"
    break
  fi
  sleep 2
done

echo "==> Waiting for backend..."
for i in $(seq 1 90); do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/health 2>/dev/null || echo "000")
  if [ "$code" = "200" ]; then
    echo "    Backend ready (HTTP $code)"
    break
  fi
  sleep 2
done

echo "==> Capturing screenshots..."
cd frontend
npx playwright test e2e/capture-menu-screenshots.spec.ts --reporter=list

echo "==> Done. See docs/menu-screenshots/v1.5.1/"
