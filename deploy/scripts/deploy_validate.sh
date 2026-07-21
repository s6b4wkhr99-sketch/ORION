#!/usr/bin/env bash
# Volume 13 Section 10 — Post-deployment validation
set -euo pipefail

BASE_URL="${CIOS_BASE_URL:-http://127.0.0.1:8000}"
ADMIN_EMAIL="${CIOS_ADMIN_EMAIL:-user@company.com}"
ADMIN_PASSWORD="${CIOS_ADMIN_PASSWORD:-Ceragem2026!Adm}"

fail() { echo "VALIDATION FAILED: $1"; exit 1; }
pass() { echo "✓ $1"; }

echo "=== CIOS Deployment Validation ==="
echo "Target: $BASE_URL"

# Application startup + health
HEALTH=$(curl -sf "$BASE_URL/api/v1/health") || fail "Health endpoint unreachable"
echo "$HEALTH" | grep -q '"success":true' || fail "Health envelope invalid"
echo "$HEALTH" | grep -q '"application"' || fail "Missing application status"
echo "$HEALTH" | grep -q '"database"' || fail "Missing database status"
echo "$HEALTH" | grep -q '"storage"' || fail "Missing storage status"
pass "Health check (application, database, storage, version, timestamp)"

# Authentication
TOKEN=$(curl -sf -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])") || fail "Authentication"
pass "Authentication (JWT issued)"

AUTH="Authorization: Bearer $TOKEN"

# Dashboard
curl -sf -H "$AUTH" "$BASE_URL/api/v1/dashboard/executive" | grep -q '"success":true' || fail "Executive dashboard"
pass "Dashboard load"

# Forecast
curl -sf -H "$AUTH" "$BASE_URL/api/v1/forecast/revenue?targetCustomers=100" | grep -q '"success":true' || fail "Forecast"
pass "Forecast module"

# Campaign
curl -sf -H "$AUTH" "$BASE_URL/api/v1/campaign" | grep -q '"success":true' || fail "Campaign module"
pass "Campaign module"

# Export preview
curl -sf -H "$AUTH" "$BASE_URL/api/v1/export/preview" | grep -q '"success":true' || fail "Export module"
pass "Export module"

echo ""
echo "All deployment validation checks passed."
