#!/usr/bin/env bash
# Full Docker Compose staging smoke: up → validate → down.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${1:-deploy/env/staging.env}"
BASE_URL="${CIOS_BASE_URL:-http://127.0.0.1:8080}"
COMPOSE="docker compose --env-file $ENV_FILE"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found — install Docker Desktop or skip with: make validate-compose"
  exit 1
fi

echo "=== CIOS Staging Compose Smoke ==="
bash scripts/validate_compose_staging.sh "$ENV_FILE"
bash scripts/validate_deploy_env.sh "$ENV_FILE" staging || {
  echo "WARN: staging env has placeholder secrets — continuing smoke for local Docker only"
}

cleanup() {
  echo "==> Stopping stack ..."
  $COMPOSE down --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "==> Building and starting stack (may take several minutes) ..."
$COMPOSE up -d --build

echo "==> Waiting for backend health (up to 3 min) ..."
for i in $(seq 1 36); do
  if curl -sf "$BASE_URL/api/v1/health" >/dev/null 2>&1; then
    echo "✓ Backend healthy"
    break
  fi
  if [ "$i" -eq 36 ]; then
    echo "ERROR: backend did not become healthy at $BASE_URL"
    $COMPOSE logs backend | tail -30
    exit 1
  fi
  sleep 5
done

CIOS_BASE_URL="$BASE_URL" bash deploy/scripts/deploy_validate.sh
echo ""
echo "✓ Staging compose smoke passed"
