#!/usr/bin/env python3
"""Rebuild metro (CBSA) and city (city_prod) rollups for existing uploads.

These rollups let the Metro Intelligence and Market Intelligence dashboards read pre-aggregated
metrics instead of scanning every customer live (metro dashboard) or capping to a top-N ZIP pool
(national Revenue-by-City). This script (re)builds them for all uploads that have customers, then
invalidates the dashboard cache so the next request serves fresh data.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from app.acquisition.rollup import build_city_rollups_for_upload  # noqa: E402
from app.cache.dashboard_cache import invalidate_dashboard_cache  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.market.market_intelligence import build_metro_rollups_for_upload  # noqa: E402
from app.models.customer import Customer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild metro (CBSA) and city rollups")
    parser.add_argument("--upload-id", type=str, default=None, help="Limit to one upload UUID")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.upload_id:
            upload_ids = [uuid.UUID(args.upload_id)]
        else:
            upload_ids = [
                row[0]
                for row in db.query(Customer.upload_id).distinct().all()
                if row[0] is not None
            ]

        if not upload_ids:
            print("No uploads with customers found.")
            return 0

        print(f"Rebuilding metro + city rollups for {len(upload_ids)} upload(s)...")
        metro_total = 0
        city_total = 0
        for uid in upload_ids:
            metro_total += build_metro_rollups_for_upload(db, uid)
            city_total += build_city_rollups_for_upload(db, uid)
            db.commit()

        invalidate_dashboard_cache()
        print(
            f"Done. {metro_total} metro rollup rows, {city_total} city rollup rows written. "
            "Dashboard cache invalidated."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
