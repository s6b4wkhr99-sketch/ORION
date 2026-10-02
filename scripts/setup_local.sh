#!/usr/bin/env bash
# First-time (or repair) local environment setup for Ceragem CIOS.
# Usage:
#   bash scripts/setup_local.sh          # primary dev Mac
#   bash scripts/setup_local.sh --field  # other Mac — login required, no dev admin seed
#   CIOS_FIELD_MAC=1 bash scripts/setup_local.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
FIELD_MAC=0
if [ "${CIOS_FIELD_MAC:-0}" = "1" ] || [ "${1:-}" = "--field" ]; then
  FIELD_MAC=1
fi

# shellcheck source=dev_common.sh
source "$ROOT/scripts/dev_common.sh"

set_env_key() {
  local file="$1"
  local key="$2"
  local value="$3"
  if grep -q "^${key}=" "$file" 2>/dev/null; then
    sed -i '' "s|^${key}=.*|${key}=${value}|" "$file" 2>/dev/null \
      || sed -i "s|^${key}=.*|${key}=${value}|" "$file"
  else
    echo "${key}=${value}" >>"$file"
  fi
}

echo "==> Ceragem CIOS local setup (v$(read_app_version))"
if [ "$FIELD_MAC" = 1 ]; then
  echo "    Mode: field / other Mac (login required, no default dev admin seed)"
fi
echo ""

# Backend venv — prefer Homebrew Python 3.12 when available
PY312=""
for candidate in /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12; do
  if [ -x "$candidate" ]; then
    PY312="$candidate"
    break
  fi
done

if [ ! -d "$BACKEND/.venv" ]; then
  echo "==> Creating Python virtualenv..."
  if [ -n "$PY312" ]; then
    "$PY312" -m venv "$BACKEND/.venv"
  else
    python3 -m venv "$BACKEND/.venv"
  fi
elif [ -n "$PY312" ] && ! "$BACKEND/.venv/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' 2>/dev/null; then
  echo "==> Recreating .venv with Python 3.12 (wrong interpreter detected)..."
  rm -rf "$BACKEND/.venv"
  "$PY312" -m venv "$BACKEND/.venv"
fi

echo "==> Installing backend dependencies..."
"$BACKEND/.venv/bin/pip" install -q -r "$BACKEND/requirements.txt"

# backend/.env
if [ ! -f "$BACKEND/.env" ]; then
  echo "==> Creating backend/.env from .env.example..."
  cp "$ROOT/.env.example" "$BACKEND/.env"
  # Local native defaults (PostgreSQL)
  if grep -q '^DATABASE_URL=sqlite' "$BACKEND/.env"; then
    sed -i '' 's|^DATABASE_URL=sqlite.*|DATABASE_URL=postgresql+psycopg2://cios:cios_dev_password@127.0.0.1:5432/cios|' "$BACKEND/.env" 2>/dev/null \
      || sed -i 's|^DATABASE_URL=sqlite.*|DATABASE_URL=postgresql+psycopg2://cios:cios_dev_password@127.0.0.1:5432/cios|' "$BACKEND/.env"
  fi
else
  echo "==> backend/.env already exists (updating auth flags)"
fi

# JWT secret — set if still default
current_secret="$(read_backend_env JWT_SECRET cios-dev-secret-change-in-production)"
if [ "$current_secret" = "cios-dev-secret-change-in-production" ] || [ -z "$current_secret" ]; then
  new_secret="$(openssl rand -hex 32 2>/dev/null || python3 -c 'import secrets; print(secrets.token_hex(32))')"
  echo "==> Generating local JWT_SECRET..."
  set_env_key "$BACKEND/.env" "JWT_SECRET" "$new_secret"
fi

# Always require login (prevents silent System Administrator dev session)
set_env_key "$BACKEND/.env" "AUTH_REQUIRED" "true"

if [ "$FIELD_MAC" = 1 ]; then
  set_env_key "$BACKEND/.env" "SEED_DEV_USERS" "false"
  set_env_key "$BACKEND/.env" "SKIP_STARTUP_SEED" "true"
  touch "$ROOT/.cios-field-mac"
fi

# APP_VERSION sync
app_ver="$(read_app_version)"
set_env_key "$BACKEND/.env" "APP_VERSION" "$app_ver"

# Frontend — always sync auth flag (existing .env.local may have AUTH_REQUIRED=false)
if [ ! -f "$FRONTEND/.env.local" ]; then
  echo "==> Creating frontend/.env.local..."
  cat >"$FRONTEND/.env.local" <<EOF
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_AUTH_REQUIRED=true
NEXT_PUBLIC_SHOW_CAMPAIGN_MODULES=false
NEXT_PUBLIC_SHOW_CUSTOMER_DATABASE=false
EOF
else
  echo "==> frontend/.env.local present (syncing NEXT_PUBLIC_AUTH_REQUIRED=true)"
  set_env_key "$FRONTEND/.env.local" "NEXT_PUBLIC_AUTH_REQUIRED" "true"
fi

if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "==> Installing frontend dependencies..."
  (cd "$FRONTEND" && npm install)
else
  echo "==> frontend node_modules present"
fi

mkdir -p "$LOG_DIR"

echo ""
echo "✓ Local setup complete."
echo ""
echo "Next steps:"
echo "  1. make postgres-up"
echo "  2. make migrate"
echo "  3. bash scripts/dev.sh start"
echo ""
echo "Check status anytime:"
echo "  bash scripts/dev.sh status"
echo ""
if [ "$FIELD_MAC" = 1 ]; then
  echo "Field Mac: sign in with your assigned account (default dev admin is NOT seeded)."
  echo "Launch: double-click \"Start CIOS (Sign In).command\" or run: bash scripts/start_field_mac.sh"
  echo "Alias (optional, add to ~/.zprofile):"
  echo "  alias cios-start='cd ~/ORION && bash scripts/start_field_mac.sh'"
  echo "If the browser skips login, it opens /login?fresh=1 to clear saved sessions."
else
  echo "Default admin: user@company.com / Ceragem2026!Adm  (local dev only)"
fi
