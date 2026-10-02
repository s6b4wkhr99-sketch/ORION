#!/usr/bin/env bash
# Field / other Mac launcher: Postgres up, CIOS start, browser opens sign-in (no saved admin session).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=dev_common.sh
source "$ROOT/scripts/dev_common.sh"

export CIOS_FIELD_LAUNCH=1
export PATH="/opt/homebrew/opt/postgresql@16/bin:/opt/homebrew/bin:/usr/local/opt/postgresql@16/bin:/usr/local/bin:${PATH:-}"

if ! check_postgres; then
  if command -v brew >/dev/null 2>&1; then
    brew services start postgresql@16 2>/dev/null || true
    sleep 3
  fi
  if ! check_postgres; then
    PGDATA="/opt/homebrew/var/postgresql@16"
    [ -d "$PGDATA" ] || PGDATA="/usr/local/var/postgresql@16"
    if [ -d "$PGDATA" ] && ! pgrep -f "$PGDATA" >/dev/null 2>&1; then
      rm -f "$PGDATA/postmaster.pid"
      pg_ctl -D "$PGDATA" -l /tmp/pg16.log start 2>/dev/null || true
      sleep 2
    fi
  fi
fi

if ! check_postgres; then
  echo "ERROR: PostgreSQL is not running at 127.0.0.1:5432"
  echo "Run: make postgres-up"
  exit 1
fi

exec bash "$ROOT/scripts/dev.sh" start --with-worker
