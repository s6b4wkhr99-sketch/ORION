#!/usr/bin/env bash
# Backend smoke tests on isolated SQLite — does not touch local PostgreSQL cios DB.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
DB_FILE="$BACKEND/.test_smoke.db"

cd "$BACKEND"
if [ ! -x ".venv/bin/python" ]; then
  echo "ERROR: Run make setup-local first"
  exit 1
fi

export DATABASE_URL="sqlite:///${DB_FILE}"
export AUTH_REQUIRED=true
export SKIP_PHYSICAL_SCHEMA=true

rm -f "$DB_FILE"
trap 'rm -f "$DB_FILE"' EXIT

echo "==> Running backend smoke tests (SQLite: .test_smoke.db)"
. .venv/bin/activate
python tests/test_smoke.py
