#!/usr/bin/env python3
"""Bulk import ZIP median income from ACS into zip_intelligence and zip_master."""

from __future__ import annotations

import argparse
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.geo.datacommons_client import fetch_zip_median_incomes  # noqa: E402
from app.geo.zip_income_import import collect_target_zips, import_zip_income, load_zcta_income  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Import ZIP median income from ACS B19013")
    parser.add_argument("--dry-run", action="store_true", help="Count target ZIPs only")
    parser.add_argument("--all-zips", action="store_true", help="Import all customer ZIPs (default)")
    parser.add_argument(
        "--no-datacommons",
        action="store_true",
        help="Disable Data Commons fallback for ZIPs missing from local ACS bulk file",
    )
    parser.add_argument(
        "--datacommons-only-missing",
        action="store_true",
        help="Only call Data Commons for ZIPs missing from ACS (no DB writes)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        targets = collect_target_zips(db)
        incomes = load_zcta_income()
        missing = sorted(z for z in targets if z not in incomes)
        matched = len(targets) - len(missing)
        print(f"ACS ZCTA rows loaded: {len(incomes):,}")
        print(f"Customer ZIP targets: {len(targets):,}")
        print(f"Expected ACS matches: {matched:,}")
        print(f"Missing from ACS bulk: {len(missing):,}")

        if not args.no_datacommons and settings.datacommons_api_key and missing:
            sample_size = min(25, len(missing))
            preview = fetch_zip_median_incomes(missing[:sample_size], api_key=settings.datacommons_api_key)
            print(
                f"Data Commons preview resolved: {len(preview):,} / {sample_size:,} "
                f"sample missing ZIPs"
            )

        if args.dry_run or args.datacommons_only_missing:
            if args.datacommons_only_missing and missing and settings.datacommons_api_key:
                filled = fetch_zip_median_incomes(missing, api_key=settings.datacommons_api_key)
                print(f"Data Commons resolved: {len(filled):,} / {len(missing):,} missing ZIPs")
            return 0

        stats = import_zip_income(
            db,
            target_zips=targets,
            use_datacommons_fallback=not args.no_datacommons,
        )
        print("ZIP income import complete:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
