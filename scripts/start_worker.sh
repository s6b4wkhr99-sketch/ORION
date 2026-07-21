#!/usr/bin/env bash
# Start CIOS async upload worker (required for large uploads when UPLOAD_ASYNC=true)
set -euo pipefail
cd "$(dirname "$0")/../backend"
source .venv/bin/activate
export WORKER_POLL_SECONDS="${WORKER_POLL_SECONDS:-5}"
echo "Starting CIOS upload worker (poll=${WORKER_POLL_SECONDS}s)..."
exec python -m app.worker.main
