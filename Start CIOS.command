#!/usr/bin/env bash
cd "$(dirname "$0")"
chmod +x scripts/dev.sh scripts/dev_foreground.sh scripts/setup_local.sh
exec bash scripts/dev.sh start "$@"
