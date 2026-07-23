#!/usr/bin/env bash
# Configure Git remote for first push (Phase C-1). Does not push automatically.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REMOTE_URL="${1:-}"
if [ -z "$REMOTE_URL" ]; then
  echo "Usage: bash scripts/setup_remote.sh <git-remote-url>"
  echo ""
  echo "Examples:"
  echo "  bash scripts/setup_remote.sh git@github.com:ceragem/cios.git"
  echo "  bash scripts/setup_remote.sh https://github.com/ceragem/cios.git"
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "Updating origin -> $REMOTE_URL"
  git remote set-url origin "$REMOTE_URL"
else
  echo "Adding origin -> $REMOTE_URL"
  git remote add origin "$REMOTE_URL"
fi

BRANCH="$(git branch --show-current)"
echo ""
echo "Remote configured. Push when ready:"
echo "  git push -u origin ${BRANCH} --tags"
