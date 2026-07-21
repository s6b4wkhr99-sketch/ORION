#!/usr/bin/env bash
# Open macOS Terminal.app and start CIOS dev servers there (fully detached from Cursor).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUNNER="$ROOT/.dev/start_in_terminal.sh"

mkdir -p "$ROOT/.dev"
cat >"$RUNNER" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
bash scripts/dev_daemon.sh restart
bash scripts/dev_daemon.sh status
echo ""
echo "Servers are running in this Terminal window."
echo "Frontend: http://localhost:3002/market-intelligence"
echo "Stop with: make dev-stop"
EOF
chmod +x "$RUNNER"

QUOTED="'$RUNNER'"
osascript -e 'tell application "Terminal" to activate' \
  -e "tell application \"Terminal\" to do script \"bash $QUOTED\""

echo "Opened Terminal.app — servers are starting there."
