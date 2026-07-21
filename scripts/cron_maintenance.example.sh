#!/usr/bin/env bash
# Volume 28.1 Phase C — example cron entries (install manually with crontab -e)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cat <<EOF
# Ceragem CIOS maintenance (adjust paths and venv)
# Daily 02:15 — MV refresh, VACUUM ANALYZE, export/temp cleanup
15 2 * * * cd ${ROOT}/backend && . .venv/bin/activate && python scripts/nightly_maintenance.py >> ${ROOT}/backend/logs/nightly.log 2>&1

# Weekly Sunday 03:00 — REINDEX + storage audit report
0 3 * * 0 cd ${ROOT}/backend && . .venv/bin/activate && python scripts/weekly_maintenance.py >> ${ROOT}/backend/logs/weekly.log 2>&1

# Optional midday cleanup
0 12 * * * cd ${ROOT}/backend && . .venv/bin/activate && python scripts/cleanup_storage.py >> ${ROOT}/backend/logs/cleanup.log 2>&1
EOF
