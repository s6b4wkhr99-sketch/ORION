#!/usr/bin/env bash
# Download large Census/ACS data assets (not stored in Git after v1.2.0).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GEO_DIR="$ROOT/backend/data/geo"
ACS_DIR="$ROOT/backend/data/acs"
mkdir -p "$GEO_DIR" "$ACS_DIR"

ZCTA_ZIP="$GEO_DIR/cb_2020_us_zcta520_500k.zip"
ZCTA_URL="https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_zcta520_500k.zip"
ACS_GEO="$ACS_DIR/acs2022_5yr_geography.dat"
ACS_GEO_URL="https://www2.census.gov/programs-surveys/acs/summary_file/2022/table-based-SF/data/5YRData/acs2022_5yr_geography.dat"
ACS_INCOME="$ACS_DIR/acsdt5y2022-b19013.dat"
ACS_INCOME_URL="https://www2.census.gov/programs-surveys/acs/summary_file/2022/table-based-SF/data/5YRData/acsdt5y2022-b19013.dat"

download() {
  local dest="$1"
  local url="$2"
  if [ -f "$dest" ]; then
    echo "✓ exists: $(basename "$dest")"
    return 0
  fi
  echo "==> Downloading $(basename "$dest") ..."
  curl -fsSL --retry 3 --connect-timeout 30 -o "$dest.part" "$url"
  mv "$dest.part" "$dest"
  echo "✓ saved: $dest"
}

download "$ZCTA_ZIP" "$ZCTA_URL"
if [ ! -f "$GEO_DIR/cb_2020_us_zcta520_500k.shp" ]; then
  echo "==> Extracting ZCTA shapefile ..."
  unzip -qo "$ZCTA_ZIP" -d "$GEO_DIR"
  echo "✓ extracted shapefile"
else
  echo "✓ shapefile present"
fi

download "$ACS_GEO" "$ACS_GEO_URL"
download "$ACS_INCOME" "$ACS_INCOME_URL"

echo ""
echo "Data assets ready under backend/data/{geo,acs}"
