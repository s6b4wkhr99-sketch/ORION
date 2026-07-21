#!/usr/bin/env bash
# Volume 13 Section 4 / 18 — Rollback to previous Docker image tag
set -euo pipefail

PREVIOUS_TAG="${1:-}"
if [ -z "$PREVIOUS_TAG" ]; then
  echo "Usage: rollback.sh <previous-image-tag>"
  echo "Example: rollback.sh cios-backend:1.0.0"
  exit 1
fi

echo "Rolling back backend to $PREVIOUS_TAG"
export CIOS_BACKEND_IMAGE="$PREVIOUS_TAG"
docker compose pull backend 2>/dev/null || true
docker compose up -d backend nginx

echo "Running deployment validation..."
"$(dirname "$0")/deploy_validate.sh"
