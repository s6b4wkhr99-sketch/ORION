#!/usr/bin/env bash
# One-click local restore from a backup timestamp or --latest
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
ENV_FILE="$BACKEND/.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ENV_FILE"
  set +a
fi

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg2://cios:cios_dev_password@127.0.0.1:5432/cios}"
export BACKUP_PATH="${BACKUP_PATH:-$BACKEND/backups}"
case "$BACKUP_PATH" in
  /*) ;;
  *) BACKUP_PATH="$BACKEND/$BACKUP_PATH" ;;
esac
export BACKUP_PATH

TARGET="${1:---latest}"
shift || true

echo "=== Ceragem CIOS local restore ==="
echo "Target:       $TARGET"
echo "DATABASE_URL: ${DATABASE_URL%%@*}@***"
echo ""

bash "$BACKEND/scripts/restore.sh" "$TARGET" "$@"
