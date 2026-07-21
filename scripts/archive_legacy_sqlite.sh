#!/usr/bin/env bash
# Move legacy SQLite database off the hot path (PostgreSQL is the active store).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
SQLITE_FILE="$BACKEND/campaign_intelligence.db"
ARCHIVE_DIR="$BACKEND/archive/legacy-sqlite"
STAMP="$(TZ=America/New_York date +%Y%m%dT%H%M%S%Z)"

if [ ! -f "$SQLITE_FILE" ]; then
  echo "No legacy SQLite file at $SQLITE_FILE — nothing to archive."
  exit 0
fi

SIZE="$(du -h "$SQLITE_FILE" | awk '{print $1}')"
mkdir -p "$ARCHIVE_DIR"
DEST="$ARCHIVE_DIR/campaign_intelligence-${STAMP}.db"

echo "Archiving legacy SQLite ($SIZE) ..."
mv "$SQLITE_FILE" "$DEST"
echo "Moved to: $DEST"
echo "Disk reclaimed from backend root: ~$SIZE"

if [ -f "$BACKEND/.env" ]; then
  if grep -q '^DATABASE_URL=.*sqlite' "$BACKEND/.env"; then
    echo ""
    echo "NOTE: backend/.env still points at SQLite."
    echo "      Run scripts/setup_2_5m_postgres.sh or copy .env.postgres to .env."
  fi
fi
