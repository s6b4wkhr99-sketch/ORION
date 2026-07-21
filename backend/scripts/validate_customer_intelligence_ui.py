#!/usr/bin/env python3
"""Validate customer intelligence API payloads for TX/PA samples and aggregate stats."""

from __future__ import annotations

import json
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from app.api.services.customers import get_customer_detail, get_customer_intelligence
from app.api.services.intelligence_framework import get_customer_intelligence_with_framework, get_intelligence_framework
from app.database import SessionLocal
from app.models.customer import Customer, CustomerIntelligence
from sqlalchemy import func

SAMPLE_IDS = {
    "TX": "e5c4419d-bba2-46a1-adf6-bbca5c2382bb",
    "PA": "9fb15ed7-b33f-4165-b40c-fd749fd7261e",
}

REQUIRED_RATIONALE_FACTORS = {
    "purchase_power",
    "pain_index",
    "lifestyle",
    "digital_engagement",
    "brand_familiarity",
    "sleep_affinity",
}


def main() -> int:
    db = SessionLocal()
    errors: list[str] = []
    try:
        rationale_count = db.query(func.count(CustomerIntelligence.customer_id)).filter(
            CustomerIntelligence.framework_summary_json.like("%recommendation_rationale%")
        ).scalar()
        v4_geo_count = db.query(func.count(CustomerIntelligence.customer_id)).filter(
            CustomerIntelligence.framework_summary_json.like("%geo-market-v4%")
        ).scalar()
        total = db.query(func.count(CustomerIntelligence.customer_id)).scalar()
        recalc = db.query(func.count(CustomerIntelligence.customer_id)).filter(
            CustomerIntelligence.generated_by.like("commercial_recalc%")
        ).scalar()

        print("=== DB Summary ===")
        print(f"total_customers={total}")
        print(f"recalc_tagged={recalc}")
        print(f"rationale_rows={rationale_count}")
        print(f"geo_v4_rows={v4_geo_count}")

        for label, cid in SAMPLE_IDS.items():
            print(f"\n=== {label} Sample {cid} ===")
            detail = get_customer_detail(db, cid)
            intel = get_customer_intelligence_with_framework(db, cid)
            framework = get_intelligence_framework(db, cid)
            if not detail or not intel:
                errors.append(f"{label}: missing customer detail/intel")
                continue

            rationale = detail.get("recommendationRationale") or (intel.get("recommendation") or {}).get("rationale")
            if not rationale:
                errors.append(f"{label}: missing recommendationRationale")
            else:
                keys = {f.get("key") for f in rationale.get("factors", []) if isinstance(f, dict)}
                missing = REQUIRED_RATIONALE_FACTORS - keys
                if missing:
                    errors.append(f"{label}: missing rationale factors {missing}")
                print(f"  product={detail.get('recommendedProduct')}")
                print(f"  brand={detail.get('brandFamiliarityIndex')}")
                print(f"  digital={detail.get('emailResponseIndex')}")
                print(f"  selection_rule={rationale.get('selection_rule')}")
                print(f"  korean_metro={rationale.get('sleep_segment')}")  # noqa: placeholder
                if framework:
                    cats = framework.get("categories") or {}
                    brand = cats.get("brand_familiarity") or {}
                    print(f"  framework_brand_level={brand.get('level')}")

            fw_rationale = (framework or {}).get("recommendationRationale")
            if not fw_rationale:
                errors.append(f"{label}: framework missing recommendationRationale")

        state_counts = (
            db.query(Customer.state, func.count(Customer.customer_id))
            .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
            .filter(Customer.state.in_(["TX", "PA"]))
            .group_by(Customer.state)
            .all()
        )
        print("\n=== TX/PA Coverage ===")
        for state, count in state_counts:
            with_r = (
                db.query(func.count(CustomerIntelligence.customer_id))
                .join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
                .filter(Customer.state == state)
                .filter(CustomerIntelligence.framework_summary_json.like("%recommendation_rationale%"))
                .scalar()
            )
            print(f"  {state}: customers={count} rationale_rows={with_r}")

        if errors:
            print("\n=== ERRORS ===")
            for err in errors:
                print(f"  - {err}")
            return 1

        print("\nValidation passed.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
