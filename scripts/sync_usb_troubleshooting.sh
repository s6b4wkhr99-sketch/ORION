#!/usr/bin/env bash
# Copy Other_Mac_Native_Troubleshooting.md (and related docs) to LeFrame_Dev USB package.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
USB_ROOT="${USB_ROOT:-/Volumes/LeFrame_Dev/ORION-v1.5.0}"
DOCS="$USB_ROOT/docs"
SRC="$ROOT/docs/Other_Mac_Native_Troubleshooting.md"
OPS="$ROOT/docs/Other_Mac_Operations_Guide.md"
DISK="$ROOT/docs/Local_Disk_Cleanup_Guide.md"
QUICKSTART="$ROOT/docs/Local_Operations_Quickstart.md"
INSTALL="$ROOT/packaging/usb-docs/START-HERE-INSTALL-OPTIONS.txt"

if [ ! -d "/Volumes/LeFrame_Dev" ]; then
  echo "ERROR: USB 'LeFrame_Dev' not mounted."
  echo "Connect the drive, then run:"
  echo "  bash scripts/sync_usb_troubleshooting.sh"
  exit 1
fi

mkdir -p "$DOCS"
cp "$SRC" "$DOCS/Other_Mac_Native_Troubleshooting.md"
cp "$OPS" "$DOCS/Other_Mac_Operations_Guide.md"
cp "$DISK" "$DOCS/Local_Disk_Cleanup_Guide.md"
cp "$QUICKSTART" "$DOCS/Local_Operations_Quickstart.md"
cp "$INSTALL" "$USB_ROOT/START-HERE-INSTALL-OPTIONS.txt"

echo "✓ Copied to $DOCS/ and START-HERE-INSTALL-OPTIONS.txt"
ls -la "$DOCS/Other_Mac_Operations_Guide.md" "$DOCS/Other_Mac_Native_Troubleshooting.md" "$USB_ROOT/START-HERE-INSTALL-OPTIONS.txt"

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
