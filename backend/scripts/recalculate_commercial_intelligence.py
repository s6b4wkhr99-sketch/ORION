#!/usr/bin/env python3
"""Apply ORION Commercial Intelligence rules to all customers in DB."""

from __future__ import annotations

import argparse
import os
import sys
import uuid

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from app.commercial.recompute import count_customers, recalculate_commercial_intelligence  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.reference.registry import COMMERCIAL_VERSION  # noqa: E402
from app.reference.seed import sync_product_catalog  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Recalculate commercial intelligence for existing customers")
    parser.add_argument("--upload-id", type=str, default=None, help="Limit to one upload UUID")
    parser.add_argument("--batch-size", type=int, default=2000)
    parser.add_argument("--commit-every", type=int, default=5000)
    parser.add_argument("--full-pipeline", action="store_true", help="Re-run entire intelligence pipeline (slow)")
    parser.add_argument("--record-versions", action="store_true", help="Store intelligence_version history (bulk bloat)")
    parser.add_argument("--sync-recommendations", action="store_true", help="Run AI recommendation sync per row (slow)")
    parser.add_argument("--dry-run", action="store_true", help="Count customers only")
    args = parser.parse_args()

    upload_id = uuid.UUID(args.upload_id) if args.upload_id else None
    db = SessionLocal()
    try:
        sync_product_catalog(db)
        total = count_customers(db, upload_id)
        print(f"Commercial version: {COMMERCIAL_VERSION}")
        print(f"Customers to recalculate: {total:,}")
        if args.dry_run or total == 0:
            return 0

        stats = recalculate_commercial_intelligence(
            db,
            upload_id=upload_id,
            batch_size=args.batch_size,
            commit_every=args.commit_every,
            full_pipeline=args.full_pipeline,
            store_full_trace=False,
            record_versions=args.record_versions,
            sync_recommendation=args.sync_recommendations,
        )
        print("Recalculation complete:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        return 1 if int(stats.get("errors", 0)) > 0 else 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
