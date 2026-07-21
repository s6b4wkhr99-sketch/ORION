#!/usr/bin/env python3
"""Build per-state ZCTA GeoJSON from Census cartographic boundary shapefile."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.geo.zcta_geo_loader import STATE_BBOX, build_state_geojson, ensure_national_shapefile


def main() -> int:
    parser = argparse.ArgumentParser(description="Build state ZCTA GeoJSON for Market Intelligence choropleth")
    parser.add_argument(
        "--state",
        action="append",
        help="Two-letter state code (repeatable). Default: all states in STATE_BBOX.",
    )
    parser.add_argument("--download-only", action="store_true", help="Only download/extract national shapefile")
    args = parser.parse_args()

    shp = ensure_national_shapefile()
    if not shp:
        print("Failed to download Census ZCTA shapefile.", file=sys.stderr)
        return 1
    print(f"Shapefile ready: {shp}")

    if args.download_only:
        return 0

    states = [s.upper() for s in args.state] if args.state else sorted(STATE_BBOX.keys())
    built = 0
    for state in states:
        result = build_state_geojson(state)
        if result:
            built += 1
            print(f"{state}: {len(result['features'])} ZCTA features")
        else:
            print(f"{state}: no features (skipped)", file=sys.stderr)

    print(f"Done — built {built}/{len(states)} state files.")
    return 0 if built else 1


if __name__ == "__main__":
    raise SystemExit(main())
