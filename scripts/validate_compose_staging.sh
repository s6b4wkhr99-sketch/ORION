#!/usr/bin/env bash
# Validate Docker Compose staging config (Phase C-4). Does not start containers.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${1:-deploy/env/staging.env}"
if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: env file not found: $ENV_FILE"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found"
  exit 1
fi

echo "==> Validating docker compose with $ENV_FILE"
docker compose --env-file "$ENV_FILE" config >/dev/null
echo "✓ docker-compose.yml + $ENV_FILE is valid"

echo ""
echo "Optional full stack smoke (requires Docker resources):"
echo "  docker compose --env-file $ENV_FILE up -d --build"
echo "  CIOS_BASE_URL=http://127.0.0.1:8080 bash deploy/scripts/deploy_validate.sh"
echo "  docker compose --env-file $ENV_FILE down"
