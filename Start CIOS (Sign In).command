#!/usr/bin/env bash
# Field Mac: double-click to start CIOS and open the sign-in screen (manual user login).
cd "$(dirname "$0")"
chmod +x scripts/start_field_mac.sh scripts/dev.sh scripts/dev_foreground.sh 2>/dev/null || true
exec bash scripts/start_field_mac.sh
