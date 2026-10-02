#!/usr/bin/env bash
cd "$(dirname "$0")"
chmod +x scripts/dev.sh scripts/dev_foreground.sh scripts/setup_local.sh scripts/start_field_mac.sh 2>/dev/null || true
# shellcheck source=dev_common.sh
source scripts/dev_common.sh
if is_field_mac; then
  exec bash scripts/start_field_mac.sh
fi
exec bash scripts/dev.sh start "$@"
