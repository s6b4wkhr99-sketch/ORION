#!/usr/bin/env bash
cd "$(dirname "$0")"
chmod +x scripts/dev_foreground.sh
exec bash scripts/dev_foreground.sh
