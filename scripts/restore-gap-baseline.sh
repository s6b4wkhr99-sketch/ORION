#!/usr/bin/env bash
# Restore Ceragem CIOS to the pre-calibration GAP analysis baseline.
# Usage (from repo root):
#   ./scripts/restore-gap-baseline.sh
set -euo pipefail

TAG="snapshot/2026-07-21-gap-baseline"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not a git repository." >&2
  exit 1
fi

if ! git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Error: tag $TAG not found. Run git fetch --tags if this is a clone." >&2
  exit 1
fi

echo "This will reset tracked files to $TAG."
echo "Uncommitted local changes will be lost."
read -r -p "Continue? [y/N] " ans
if [[ "${ans:-}" != "y" && "${ans:-}" != "Y" ]]; then
  echo "Aborted."
  exit 0
fi

git checkout "$TAG" -- .
git clean -fd --exclude=.env --exclude=.env.* --exclude=backend/.env --exclude=frontend/.env.local
echo "Restored to $TAG"
echo "Tip: to stay on a branch at this snapshot: git checkout -B restore/gap-baseline $TAG"
