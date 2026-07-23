#!/usr/bin/env bash
# PostgreSQL acceptance — CI service container or local PG (TEST_DATABASE_URL).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
DB_URL="${TEST_DATABASE_URL:-${DATABASE_URL:-postgresql+psycopg2://cios:cios_ci_password@127.0.0.1:5432/cios}}"

PYTHON="python3"
if [ -x "$BACKEND/.venv/bin/python" ]; then
  PYTHON="$BACKEND/.venv/bin/python"
fi

export DATABASE_URL="$DB_URL"
export TEST_DATABASE_URL="$DB_URL"
export AUTH_REQUIRED=true
export SKIP_PHYSICAL_SCHEMA=false

cd "$BACKEND"

echo "==> PostgreSQL acceptance tests"
echo "    DATABASE_URL=${DB_URL}"

"$PYTHON" -m pip install -q -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt

echo "==> alembic upgrade head"
"$PYTHON" -m alembic upgrade head

echo "==> init_postgres (seed users + reference schema)"
"$PYTHON" scripts/init_postgres.py

echo "==> Phase 3 PostgreSQL checks"
"$PYTHON" tests/test_phase3_postgres.py

echo "✓ PostgreSQL acceptance passed"
