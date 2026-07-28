#!/usr/bin/env bash
# Volume 13 Section 15 — Daily backup (database, uploads, config snapshot)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/db_url.sh
source "$(dirname "$0")/lib/db_url.sh"

BACKUP_ROOT="${BACKUP_PATH:-$ROOT/backups}"
case "$BACKUP_ROOT" in
  /*) ;;
  *) BACKUP_ROOT="$ROOT/$BACKUP_ROOT" ;;
esac
STAMP="$(TZ=America/New_York date +%Y%m%dT%H%M%S%Z)"
DEST="$BACKUP_ROOT/$STAMP"
mkdir -p "$DEST"

echo "CIOS backup started -> $DEST"

if [ -n "${DATABASE_URL:-}" ]; then
  if is_postgres_url "$DATABASE_URL"; then
    PG_URI="$(to_pg_uri "$DATABASE_URL")"
    export PATH="/opt/homebrew/opt/postgresql@16/bin:/opt/homebrew/bin:$PATH"
    if ! command -v pg_dump >/dev/null 2>&1; then
      echo "ERROR: pg_dump not found. Install PostgreSQL client tools." >&2
      exit 1
    fi
    pg_dump --no-owner --no-acl --clean --if-exists "$PG_URI" > "$DEST/database.sql"
    if [ ! -s "$DEST/database.sql" ]; then
      echo "ERROR: pg_dump produced an empty database.sql" >&2
      exit 1
    fi
    echo "  database.sql ($(du -h "$DEST/database.sql" | awk '{print $1}'))"
    gzip -9 "$DEST/database.sql"
    echo "  database.sql.gz ($(du -h "$DEST/database.sql.gz" | awk '{print $1}'))"
  elif is_sqlite_url "$DATABASE_URL"; then
    DB_FILE="$(resolve_sqlite_path "$DATABASE_URL" "$ROOT")"
    if [ -f "$DB_FILE" ]; then
      cp "$DB_FILE" "$DEST/campaign_intelligence.db"
      echo "  campaign_intelligence.db ($(du -h "$DEST/campaign_intelligence.db" | awk '{print $1}'))"
    else
      echo "WARN: SQLite file not found: $DB_FILE" >&2
    fi
  fi
fi

UPLOAD_DIR="${UPLOAD_DIR:-uploads}"
# Skip uploads.tar.gz on dev Mac when backend/uploads/ already exists (saves ~1–3 GB).
# Set BACKUP_INCLUDE_UPLOADS=true for off-machine restore bundles.
if [ "${BACKUP_INCLUDE_UPLOADS:-false}" = "true" ] && [ -d "$ROOT/$UPLOAD_DIR" ]; then
  tar -czf "$DEST/uploads.tar.gz" -C "$ROOT" "$UPLOAD_DIR"
  echo "  uploads.tar.gz ($(du -h "$DEST/uploads.tar.gz" | awk '{print $1}'))"
fi

if [ -f "$ROOT/.env" ]; then
  cp "$ROOT/.env" "$DEST/env.snapshot"
  echo "  env.snapshot"
fi

find "$BACKUP_ROOT" -maxdepth 1 -type d -mtime +90 -exec rm -rf {} + 2>/dev/null || true

echo "CIOS backup completed -> $DEST"
