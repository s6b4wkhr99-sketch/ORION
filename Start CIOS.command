#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "Starting Ceragem CIOS dev servers..."
bash scripts/dev_daemon.sh restart
bash scripts/dev_daemon.sh status
echo ""
echo "Frontend: http://localhost:3002/market-intelligence"
echo "Keep this Terminal window open while you work."
echo "To stop servers: make dev-stop"
exec bash -l
