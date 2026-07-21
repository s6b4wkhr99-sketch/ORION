#!/usr/bin/env bash
# Ceragem CIOS — PostgreSQL + 2.5M bulk upload setup
# Requires: Docker (recommended) or local PostgreSQL on port 5432
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
COMPOSE_FILE="$ROOT/docker-compose.postgres.yml"
ENV_POSTGRES="$BACKEND/.env.postgres"
ENV_ACTIVE="$BACKEND/.env"
PG_URL="${DATABASE_URL:-postgresql+psycopg2://cios:cios_dev_password@127.0.0.1:5432/cios}"

docker_cmd() {
  if command -v docker >/dev/null 2>&1; then
    docker "$@"
    return
  fi
  for candidate in /usr/local/bin/docker /opt/homebrew/bin/docker \
    /Applications/Docker.app/Contents/Resources/bin/docker; do
    if [ -x "$candidate" ]; then
      "$candidate" "$@"
      return
    fi
  done
  return 1
}

brew_postgres_start() {
  export PATH="/opt/homebrew/opt/postgresql@16/bin:/opt/homebrew/bin:$PATH"
  if ! command -v brew >/dev/null 2>&1 && [ -x /opt/homebrew/bin/brew ]; then
    export PATH="/opt/homebrew/bin:$PATH"
  fi
  if ! command -v brew >/dev/null 2>&1; then
    echo "ERROR: Neither Docker nor Homebrew found."
    exit 1
  fi
  if ! brew list postgresql@16 >/dev/null 2>&1; then
    echo "==> Installing PostgreSQL 16 via Homebrew..."
    brew install postgresql@16
  fi
  echo "==> Starting PostgreSQL via Homebrew..."
  brew services start postgresql@16
  sleep 3
  if ! pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
    echo "ERROR: PostgreSQL not accepting connections on 127.0.0.1:5432"
    exit 1
  fi
  echo "==> Ensuring cios role/database..."
  psql -h 127.0.0.1 -d postgres -v ON_ERROR_STOP=1 <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'cios') THEN
    CREATE ROLE cios WITH LOGIN PASSWORD 'cios_dev_password';
  END IF;
END
$$;
SELECT 'CREATE DATABASE cios OWNER cios'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'cios')\gexec
GRANT ALL PRIVILEGES ON DATABASE cios TO cios;
SQL
}

echo "==> CIOS 2.5M PostgreSQL setup"
echo "    Project: $ROOT"

if [ -f "$COMPOSE_FILE" ] && docker_cmd compose version >/dev/null 2>&1; then
  echo "==> Starting PostgreSQL container..."
  docker_cmd compose -f "$COMPOSE_FILE" up -d
  echo "==> Waiting for PostgreSQL..."
  for _ in $(seq 1 30); do
    if docker_cmd compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U cios >/dev/null 2>&1; then
      echo "    PostgreSQL is ready."
      break
    fi
    sleep 2
  done
else
  echo "WARN: Docker not available — using Homebrew PostgreSQL"
  brew_postgres_start
fi

if [ -f "$ENV_POSTGRES" ]; then
  echo "==> Activating backend/.env.postgres -> backend/.env"
  cp "$ENV_POSTGRES" "$ENV_ACTIVE"
fi

export DATABASE_URL="$PG_URL"
cd "$BACKEND"

if [ ! -d .venv ]; then
  echo "ERROR: backend/.venv missing — create venv and pip install -r requirements.txt first."
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Running Alembic migrations..."
alembic upgrade head

echo "==> Initializing schema + seeds..."
python scripts/init_postgres.py

echo ""
echo "==> Setup complete. Start services in separate terminals:"
echo "    1) Backend:  cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
echo "    2) Worker:   cd backend && source .venv/bin/activate && python -m app.worker.main"
echo "    3) Frontend: cd frontend && npm run dev"
echo ""
echo "    Upload 2.5M customers at http://localhost:3002/import"
echo "    DATABASE_URL=$PG_URL"
