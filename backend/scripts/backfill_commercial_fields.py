#!/usr/bin/env python3
"""Backfill commercial fields on customer_intelligence from recommended_product."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy.orm import Session  # noqa: E402

from app.commercial.catalog import product_by_code, warm_catalog_cache  # noqa: E402
from app.commercial.engine import cap_promotion, default_promotion_amount  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.customer import CustomerIntelligence  # noqa: E402
from app.reference.registry import ACTIVE_STANDING_PROMOTIONS, COMMERCIAL_VERSION  # noqa: E402


def _commercial_fields(product_code: str | None) -> tuple[float | None, str | None]:
    if not product_code:
        return None, None
    proposed = default_promotion_amount(product_code)
    promotion = cap_promotion(product_code, proposed)["recommended_promotion"]
    catalog = product_by_code(product_code)
    standing = ACTIVE_STANDING_PROMOTIONS.get(product_code)
    promo_code = standing["promo_code"] if standing and promotion else None
    return promotion, promo_code


def backfill(db: Session, batch_size: int = 5000, dry_run: bool = False) -> dict:
    updated = 0
    last_id = None
    while True:
        q = db.query(CustomerIntelligence).order_by(CustomerIntelligence.id)
        if last_id is not None:
            q = q.filter(CustomerIntelligence.id > last_id)
        rows = q.limit(batch_size).all()
        if not rows:
            break
        for row in rows:
            last_id = row.id
            promotion, promo_code = _commercial_fields(row.recommended_product)
            row.recommended_promotion = promotion
            row.promo_code = promo_code
            if row.commercial_version is None:
                row.commercial_version = COMMERCIAL_VERSION
            updated += 1
        if dry_run:
            db.rollback()
            break
        db.commit()
    return {"updated": updated, "dry_run": dry_run}


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill promo_code and recommended_promotion")
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        warm_catalog_cache(db)
        stats = backfill(db, batch_size=args.batch_size, dry_run=args.dry_run)
        print(stats)
    finally:
        db.close()


if __name__ == "__main__":
    main()
