#!/usr/bin/env bash
# Create a versioned source archive (e.g. for iCloud / offline backup).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VERSION="$(cat VERSION 2>/dev/null || echo "unknown")"
DATE="$(date +%Y%m%d)"
OUT_DIR="${1:-$HOME/Desktop/CIOS-Backups}"
ARCHIVE="$OUT_DIR/cios-${VERSION}-${DATE}.zip"

mkdir -p "$OUT_DIR"
git archive --format=zip -o "$ARCHIVE" HEAD

echo "✓ Release archive: $ARCHIVE"
echo "  Version: $VERSION"
echo "  Commit:  $(git rev-parse --short HEAD)"
