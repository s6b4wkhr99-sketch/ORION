#!/usr/bin/env bash
# Generate cryptographically strong secrets for deploy env files.
set -euo pipefail

JWT="$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")"
PG="$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")"

echo "# Paste into deploy/env/production.env or staging.env (do NOT commit filled files)"
echo "JWT_SECRET=${JWT}"
echo "POSTGRES_PASSWORD=${PG}"
echo ""
echo "# Example DATABASE_URL (adjust user/db/host):"
echo "DATABASE_URL=postgresql+psycopg2://cios:${PG}@postgres:5432/cios_prod"
