#!/usr/bin/env bash
# Other-Mac / field deployment: require login, skip default dev admin seed.
# Usage: bash scripts/setup_field_mac.sh
set -euo pipefail

export CIOS_FIELD_MAC=1
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$ROOT/scripts/setup_local.sh" --field
