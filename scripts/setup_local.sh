#!/usr/bin/env bash
# First-time (or repair) local environment setup for Ceragem CIOS.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
# shellcheck source=dev_common.sh
source "$ROOT/scripts/dev_common.sh"

echo "==> Ceragem CIOS local setup (v$(read_app_version))"
echo ""

# Backend venv
if [ ! -d "$BACKEND/.venv" ]; then
  echo "==> Creating Python virtualenv..."
  python3 -m venv "$BACKEND/.venv"
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
  echo "==> backend/.env already exists (unchanged)"
fi

# JWT secret — set if still default
current_secret="$(read_backend_env JWT_SECRET cios-dev-secret-change-in-production)"
if [ "$current_secret" = "cios-dev-secret-change-in-production" ] || [ -z "$current_secret" ]; then
  new_secret="$(openssl rand -hex 32 2>/dev/null || python3 -c 'import secrets; print(secrets.token_hex(32))')"
  echo "==> Generating local JWT_SECRET..."
  if grep -q '^JWT_SECRET=' "$BACKEND/.env"; then
    sed -i '' "s|^JWT_SECRET=.*|JWT_SECRET=${new_secret}|" "$BACKEND/.env" 2>/dev/null \
      || sed -i "s|^JWT_SECRET=.*|JWT_SECRET=${new_secret}|" "$BACKEND/.env"
  else
    echo "JWT_SECRET=${new_secret}" >>"$BACKEND/.env"
  fi
fi

# Auth on for local pilot
if grep -q '^AUTH_REQUIRED=' "$BACKEND/.env"; then
  sed -i '' 's|^AUTH_REQUIRED=.*|AUTH_REQUIRED=true|' "$BACKEND/.env" 2>/dev/null \
    || sed -i 's|^AUTH_REQUIRED=.*|AUTH_REQUIRED=true|' "$BACKEND/.env"
else
  echo "AUTH_REQUIRED=true" >>"$BACKEND/.env"
fi

# APP_VERSION sync
app_ver="$(read_app_version)"
if grep -q '^APP_VERSION=' "$BACKEND/.env"; then
  sed -i '' "s|^APP_VERSION=.*|APP_VERSION=${app_ver}|" "$BACKEND/.env" 2>/dev/null \
    || sed -i "s|^APP_VERSION=.*|APP_VERSION=${app_ver}|" "$BACKEND/.env"
else
  echo "APP_VERSION=${app_ver}" >>"$BACKEND/.env"
fi

# Frontend
if [ ! -f "$FRONTEND/.env.local" ]; then
  echo "==> Creating frontend/.env.local..."
  cat >"$FRONTEND/.env.local" <<EOF
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_AUTH_REQUIRED=true
NEXT_PUBLIC_SHOW_CAMPAIGN_MODULES=false
NEXT_PUBLIC_SHOW_CUSTOMER_DATABASE=false
EOF
else
  echo "==> frontend/.env.local already exists (unchanged)"
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
echo "Default admin: user@company.com / Ceragem2026!Adm  (local dev only)"
