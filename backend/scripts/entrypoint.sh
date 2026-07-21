#!/usr/bin/env bash
set -euo pipefail

cd /app

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running database migrations..."
  alembic upgrade head || echo "Migration skipped or failed — continuing startup"
fi

exec "$@"
