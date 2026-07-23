#!/usr/bin/env bash
# Backend smoke tests on isolated SQLite — does not touch local PostgreSQL cios DB.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
DB_FILE="$BACKEND/.test_smoke.db"

cd "$BACKEND"
PYTHON="python3"
if [ -x ".venv/bin/python" ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate
  PYTHON="python"
fi

export DATABASE_URL="sqlite:///${DB_FILE}"
export AUTH_REQUIRED=true
export SKIP_PHYSICAL_SCHEMA=true
export UPLOAD_ASYNC=true

rm -f "$DB_FILE"
trap 'rm -f "$DB_FILE"' EXIT

echo "==> Running backend smoke tests (SQLite: .test_smoke.db)"
"$PYTHON" tests/test_smoke.py
