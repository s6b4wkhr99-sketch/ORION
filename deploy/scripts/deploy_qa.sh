#!/usr/bin/env bash
# Deploy or refresh CIOS on a QA host (run on server or via GitHub Actions SSH).
set -euo pipefail

APP_DIR="${CIOS_APP_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
ENV_FILE="${CIOS_ENV_FILE:-$APP_DIR/deploy/env/qa.env}"
BASE_URL="${CIOS_BASE_URL:-http://127.0.0.1:8080}"

cd "$APP_DIR"

echo "=== CIOS QA Deploy ==="
echo "App dir:  $APP_DIR"
echo "Env file: $ENV_FILE"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: env file not found: $ENV_FILE"
  exit 1
fi

bash scripts/validate_deploy_env.sh "$ENV_FILE" qa || true

echo "==> docker compose up --build"
docker compose --env-file "$ENV_FILE" up -d --build

echo "==> Waiting for health ..."
for i in $(seq 1 36); do
  if curl -sf "$BASE_URL/api/v1/health" >/dev/null 2>&1; then
    break
  fi
  [ "$i" -eq 36 ] && { echo "Health check failed"; exit 1; }
  sleep 5
done

CIOS_BASE_URL="$BASE_URL" bash deploy/scripts/deploy_validate.sh
echo "✓ QA deploy complete"
