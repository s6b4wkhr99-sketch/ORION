#!/usr/bin/env bash
# Copy Other_Mac_Native_Troubleshooting.md (and related docs) to LeFrame_Dev USB package.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
USB_ROOT="${USB_ROOT:-/Volumes/LeFrame_Dev/ORION-v1.5.0}"
DOCS="$USB_ROOT/docs"
SRC="$ROOT/docs/Other_Mac_Native_Troubleshooting.md"
QUICKSTART="$ROOT/docs/Local_Operations_Quickstart.md"

if [ ! -d "/Volumes/LeFrame_Dev" ]; then
  echo "ERROR: USB 'LeFrame_Dev' not mounted."
  echo "Connect the drive, then run:"
  echo "  bash scripts/sync_usb_troubleshooting.sh"
  exit 1
fi

mkdir -p "$DOCS"
cp "$SRC" "$DOCS/Other_Mac_Native_Troubleshooting.md"
cp "$QUICKSTART" "$DOCS/Local_Operations_Quickstart.md"

# Cross-link standalone copy (Quickstart links stay valid inside ORION source; USB copy is reference)
echo "✓ Copied to $DOCS/"
ls -la "$DOCS/Other_Mac_Native_Troubleshooting.md" "$DOCS/Local_Operations_Quickstart.md"

if [ -f "$USB_ROOT/README-USB.md" ]; then
  if ! grep -q "Other_Mac_Native_Troubleshooting" "$USB_ROOT/README-USB.md"; then
    # Insert docs row after Other_Mac_Operations_Guide line if present
    if grep -q "Other_Mac_Operations_Guide" "$USB_ROOT/README-USB.md"; then
      sed -i '' '/Other_Mac_Operations_Guide/a\
| `docs/Other_Mac_Native_Troubleshooting.md` | **다른 Mac 문제 해결 (상황별)** |
' "$USB_ROOT/README-USB.md" 2>/dev/null || true
    fi
    echo "✓ Updated README-USB.md (if sed supported)"
  fi
fi

echo ""
echo "Done. USB docs ready under: $DOCS/"
