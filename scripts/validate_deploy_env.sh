#!/usr/bin/env bash
# Validate deploy environment files before staging/production/QA deploy.
set -euo pipefail

ENV_FILE="${1:-}"
PROFILE="${2:-production}"

if [ -z "$ENV_FILE" ] || [ ! -f "$ENV_FILE" ]; then
  echo "Usage: validate_deploy_env.sh <env-file> [production|staging|qa|development]"
  exit 1
fi

fail=0
warn=0

pass() { echo "✓ $1"; }
fail_msg() { echo "✗ $1"; fail=1; }
warn_msg() { echo "! $1"; warn=1; }

get_val() {
  local key="$1"
  grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '\r' || true
}

is_placeholder() {
  local val="$1"
  case "$val" in
    ""|REPLACE_ME|REPLACE_WITH_STRONG_SECRET|replace-with-*|change-me*|cios-dev-secret*|cios_dev_password|*example.com*)
      return 0
      ;;
  esac
  return 1
}

echo "=== CIOS Deploy Env Validation ==="
echo "File:    $ENV_FILE"
echo "Profile: $PROFILE"
echo ""

JWT="$(get_val JWT_SECRET)"
PG_PASS="$(get_val POSTGRES_PASSWORD)"
AUTH="$(get_val AUTH_REQUIRED)"
DEBUG="$(get_val DEBUG)"
ENV_NAME="$(get_val ENVIRONMENT)"

case "$PROFILE" in
  development)
    pass "development profile — placeholder secrets allowed"
    exit 0
    ;;
  production)
    if is_placeholder "$JWT"; then fail_msg "JWT_SECRET must be rotated (use: bash scripts/generate_secrets.sh)"; else pass "JWT_SECRET set"; fi
    if is_placeholder "$PG_PASS"; then fail_msg "POSTGRES_PASSWORD must be rotated"; else pass "POSTGRES_PASSWORD set"; fi
    if [ "$AUTH" != "true" ]; then fail_msg "AUTH_REQUIRED must be true in production"; else pass "AUTH_REQUIRED=true"; fi
    if [ "$DEBUG" = "true" ]; then fail_msg "DEBUG must be false in production"; else pass "DEBUG=false"; fi
    ;;
  staging)
    if is_placeholder "$JWT"; then fail_msg "JWT_SECRET must be rotated for staging"; else pass "JWT_SECRET set"; fi
    if is_placeholder "$PG_PASS"; then warn_msg "POSTGRES_PASSWORD looks like a template — rotate before external staging"; else pass "POSTGRES_PASSWORD set"; fi
    if [ "$AUTH" != "true" ]; then warn_msg "AUTH_REQUIRED should be true for staging"; else pass "AUTH_REQUIRED=true"; fi
    ;;
  qa)
    if is_placeholder "$JWT"; then warn_msg "JWT_SECRET is placeholder — set GitHub secret QA_JWT_SECRET or update qa.env on host"; else pass "JWT_SECRET set"; fi
    if is_placeholder "$PG_PASS"; then warn_msg "POSTGRES_PASSWORD is template — OK for first QA bootstrap"; else pass "POSTGRES_PASSWORD set"; fi
    pass "QA profile (warnings only unless --strict)"
    if [ "${STRICT:-0}" = "1" ] && [ "$warn" = "1" ]; then fail=1; fi
    ;;
  *)
    echo "Unknown profile: $PROFILE"
    exit 1
    ;;
esac

if [ "$fail" -eq 0 ]; then
  echo ""
  echo "Validation passed ($PROFILE)."
  exit 0
fi

echo ""
echo "Validation FAILED — fix env file before deploy."
exit 1
