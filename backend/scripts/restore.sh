#!/usr/bin/env bash
# Restore CIOS backup (PostgreSQL dump, uploads, optional .env snapshot)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/db_url.sh
source "$(dirname "$0")/lib/db_url.sh"

BACKUP_ROOT="${BACKUP_PATH:-$ROOT/backups}"
case "$BACKUP_ROOT" in
  /*) ;;
  *) BACKUP_ROOT="$ROOT/$BACKUP_ROOT" ;;
esac
RESTORE_UPLOADS="${RESTORE_UPLOADS:-true}"
RESTORE_ENV="${RESTORE_ENV:-false}"
ASSUME_YES="${ASSUME_YES:-false}"

usage() {
  cat <<EOF
Usage: $(basename "$0") <backup-dir|timestamp|--latest> [options]

Options:
  --no-uploads    Skip restoring uploads.tar.gz
  --with-env      Restore env.snapshot over backend/.env
  --yes           Skip confirmation prompt
EOF
}

if [ $# -lt 1 ]; then
  usage >&2
  exit 1
fi

TARGET="$1"
shift

while [ $# -gt 0 ]; do
  case "$1" in
    --no-uploads) RESTORE_UPLOADS=false ;;
    --with-env) RESTORE_ENV=true ;;
    --yes) ASSUME_YES=true ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

if [ "$TARGET" = "--latest" ]; then
  DEST="$(find "$BACKUP_ROOT" -maxdepth 1 -mindepth 1 -type d | sort | tail -1)"
else
  if [ -d "$TARGET" ]; then
    DEST="$TARGET"
  elif [ -d "$BACKUP_ROOT/$TARGET" ]; then
    DEST="$BACKUP_ROOT/$TARGET"
  else
    echo "ERROR: Backup not found: $TARGET" >&2
    exit 1
  fi
fi

if [ -z "${DEST:-}" ] || [ ! -d "$DEST" ]; then
  echo "ERROR: No backup directory found under $BACKUP_ROOT" >&2
  exit 1
fi

echo "Restore source: $DEST"

if [ -z "${DATABASE_URL:-}" ]; then
  if [ -f "$ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$ROOT/.env"
    set +a
  else
    echo "ERROR: DATABASE_URL is not set and .env is missing." >&2
    exit 1
  fi
fi

if [ "$ASSUME_YES" != "true" ]; then
  echo ""
  echo "This will overwrite the current PostgreSQL database and optionally uploads."
  read -r -p "Continue? [y/N] " reply
  case "$reply" in
    y|Y|yes|YES) ;;
    *) echo "Aborted."; exit 0 ;;
  esac
fi

export PATH="/opt/homebrew/opt/postgresql@16/bin:/opt/homebrew/bin:$PATH"

if is_postgres_url "$DATABASE_URL"; then
  SQL_FILE=""
  if [ -f "$DEST/database.sql.gz" ] && [ -s "$DEST/database.sql.gz" ]; then
    SQL_FILE="$DEST/database.sql.gz"
  elif [ -f "$DEST/database.sql" ] && [ -s "$DEST/database.sql" ]; then
    SQL_FILE="$DEST/database.sql"
  else
    echo "ERROR: database.sql or database.sql.gz missing or empty in backup." >&2
    exit 1
  fi
  if ! command -v psql >/dev/null 2>&1; then
    echo "ERROR: psql not found. Install PostgreSQL client tools." >&2
    exit 1
  fi
  PG_URI="$(to_pg_uri "$DATABASE_URL")"
  echo "Restoring PostgreSQL from $(basename "$SQL_FILE") ..."
  if [[ "$SQL_FILE" == *.gz ]]; then
    if ! command -v gunzip >/dev/null 2>&1; then
      echo "ERROR: gunzip not found (required for database.sql.gz)." >&2
      exit 1
    fi
    gunzip -c "$SQL_FILE" | psql "$PG_URI" -v ON_ERROR_STOP=1
  else
    psql "$PG_URI" -v ON_ERROR_STOP=1 -f "$SQL_FILE"
  fi
  echo "  PostgreSQL restore complete."
elif is_sqlite_url "$DATABASE_URL"; then
  if [ ! -f "$DEST/campaign_intelligence.db" ]; then
    echo "ERROR: campaign_intelligence.db missing in backup." >&2
    exit 1
  fi
  DB_FILE="$(resolve_sqlite_path "$DATABASE_URL" "$ROOT")"
  cp "$DEST/campaign_intelligence.db" "$DB_FILE"
  echo "  SQLite restore complete -> $DB_FILE"
else
  echo "ERROR: Unsupported DATABASE_URL." >&2
  exit 1
fi

if [ "$RESTORE_UPLOADS" = "true" ] && [ -f "$DEST/uploads.tar.gz" ]; then
  UPLOAD_DIR="${UPLOAD_DIR:-uploads}"
  rm -rf "$ROOT/$UPLOAD_DIR"
  tar -xzf "$DEST/uploads.tar.gz" -C "$ROOT"
  echo "  uploads restored -> $ROOT/$UPLOAD_DIR"
fi

if [ "$RESTORE_ENV" = "true" ] && [ -f "$DEST/env.snapshot" ]; then
  cp "$DEST/env.snapshot" "$ROOT/.env"
  echo "  .env restored from env.snapshot"
fi

echo "CIOS restore completed from $DEST"
