#!/usr/bin/env bash
# One-click local backup: PostgreSQL dump + uploads + .env snapshot
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
ENV_FILE="$BACKEND/.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ENV_FILE"
  set +a
else
  echo "WARN: $ENV_FILE not found; using existing environment." >&2
fi

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg2://cios:cios_dev_password@127.0.0.1:5432/cios}"
export BACKUP_PATH="${BACKUP_PATH:-$BACKEND/backups}"
case "$BACKUP_PATH" in
  /*) ;;
  *) BACKUP_PATH="$BACKEND/$BACKUP_PATH" ;;
esac
export BACKUP_PATH

echo "=== Ceragem CIOS local backup ==="
echo "DATABASE_URL: ${DATABASE_URL%%@*}@***"
echo "Backup root:  $BACKUP_PATH"
echo ""

bash "$BACKEND/scripts/backup.sh"

LATEST="$(find "$BACKUP_PATH" -maxdepth 1 -mindepth 1 -type d | sort | tail -1)"
echo ""
echo "Latest backup: $LATEST"
ls -lah "$LATEST"
