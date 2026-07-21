#!/usr/bin/env python3
"""Full-universe buyer profile GAP analysis with CA / geographic bias correction.

Usage (from backend/):
  PYTHONPATH=. python scripts/buyer_gap_full.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.campaign.buyer_profile_gap import (
    MASTER_TO_TOKEN,
    build_profile_matrix,
    build_prospect_state_gap,
    calibration_backlog,
    compute_reweight_table,
    distribution_gap,
    load_buyer_rows,
    prospect_token_distribution,
    reweighted_buyer_sku_distribution,
)
from app.intelligence.buyer_gap_mapping import (
    buyer_compare_sku,
    index_level,
    master_series,
    purchase_series,
)
from app.intelligence.product_ladders import resolve_active_ladder

DEFAULT_LEGACY = Path(
    "/Users/josephpark/Desktop/01. Ceragem Consulting/02. Ceragem Dashboard Project/"
    "Ceragem Email Campagin Project/00. Ceragem Purchased Customer Archives/"
    "Ceragem Purchaser Archives 2011-2024.xlsx"
)
DEFAULT_SHOPIFY = Path(
    "/Users/josephpark/Desktop/01. Ceragem Consulting/02. Ceragem Dashboard Project/"
    "Ceragem Email Campagin Project/00. Ceragem Purchased Customer Archives/"
    "Ceragem Purchaser Archives 2024-2026.05.csv"
)


def load_orion_intel(engine, emails: list[str]) -> dict[str, dict]:
    if not emails:
        return {}
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT DISTINCT ON (LOWER(TRIM(c.email)))
                       LOWER(TRIM(c.email)) AS email,
                       ci.ceragem_segment,
                       ci.prizm_proxy_segment,
                       ci.purchase_power_index,
                       ci.lifestyle_index,
                       ci.pain_index,
                       ci.recommended_product,
                       c.state
                FROM customers c
                JOIN customer_intelligence ci ON ci.customer_id = c.customer_id
                WHERE LOWER(TRIM(c.email)) = ANY(:emails)
                ORDER BY LOWER(TRIM(c.email)), ci.generated_at DESC NULLS LAST
                """
            ),
            {"emails": emails},
        ).mappings().all()
    return {r["email"]: dict(r) for r in rows}


def load_prospect_aggregates(engine) -> tuple[dict[str, int], Counter[str], dict[str, Counter[str]]]:
    with engine.connect() as conn:
        rec_rows = conn.execute(
            text(
                """
                SELECT recommended_product, COUNT(*) AS n
                FROM customer_intelligence
                WHERE recommended_product IS NOT NULL
                GROUP BY recommended_product
                """
            )
        ).mappings().all()
        state_rows = conn.execute(
            text(
                """
                SELECT c.state, COUNT(*) AS n
                FROM customers c
                JOIN customer_intelligence ci ON ci.customer_id = c.customer_id
                WHERE c.state IS NOT NULL AND TRIM(c.state) <> ''
                GROUP BY c.state
                """
            )
        ).mappings().all()
        state_rec_rows = conn.execute(
            text(
                """
                SELECT c.state, ci.recommended_product, COUNT(*) AS n
                FROM customers c
                JOIN customer_intelligence ci ON ci.customer_id = c.customer_id
                WHERE c.state IS NOT NULL AND TRIM(c.state) <> ''
                  AND ci.recommended_product IS NOT NULL
                GROUP BY c.state, ci.recommended_product
                """
            )
        ).mappings().all()

    rec_counts = {r["recommended_product"]: r["n"] for r in rec_rows}
    state_counts = Counter({r["state"]: r["n"] for r in state_rows})
    by_state_rec: dict[str, Counter[str]] = {}
    for r in state_rec_rows:
        by_state_rec.setdefault(r["state"], Counter())[r["recommended_product"]] = r["n"]
    return rec_counts, state_counts, by_state_rec


def analyze_intel_rows(rows, intel_map: dict[str, dict]) -> dict:
    records = []
    for row in rows:
        intel = intel_map.get(row.email)
        if not intel:
            continue
        compare_sku, mapping_rule = buyer_compare_sku(
            row.product_raw,
            ceragem_segment=intel.get("ceragem_segment"),
            prizm_proxy_segment=intel.get("prizm_proxy_segment"),
            purchase_power_index=intel.get("purchase_power_index"),
            lifestyle_index=intel.get("lifestyle_index"),
            pain_index=intel.get("pain_index"),
            customer_state=intel.get("state"),
        )
        recommended = intel.get("recommended_product")
        pain_cat = index_level(intel.get("pain_index"))
        ladder, _ = resolve_active_ladder(
            ceragem_segment=intel.get("ceragem_segment"),
            prizm_segment=intel.get("prizm_proxy_segment"),
            pain_index_category=pain_cat,
        )
        compare_rank = ladder.index(compare_sku) if compare_sku in ladder else None
        rec_rank = ladder.index(recommended) if recommended in ladder else None
        records.append(
            {
                "email": row.email,
                "purchased_token": row.sku_token,
                "compare_sku": compare_sku,
                "recommended_product": recommended,
                "mapping_rule": mapping_rule,
                "exact_hit": compare_sku == recommended,
                "series_match": master_series(compare_sku) == master_series(recommended),
                "ladder_rank_gap": (compare_rank - rec_rank)
                if compare_rank is not None and rec_rank is not None
                else None,
                "buyer_state": row.state,
                "prospect_state": intel.get("state"),
            }
        )

    n = len(records)
    if not n:
        return {"intel_matched_rows": 0}
    ladder_gaps = [r["ladder_rank_gap"] for r in records if r["ladder_rank_gap"] is not None]
    return {
        "intel_matched_rows": n,
        "unique_emails": len({r["email"] for r in records}),
        "exact_hit_rate_pct": round(100 * sum(1 for r in records if r["exact_hit"]) / n, 2),
        "series_match_rate_pct": round(100 * sum(1 for r in records if r["series_match"]) / n, 2),
        "avg_ladder_rank_gap": round(sum(ladder_gaps) / len(ladder_gaps), 2) if ladder_gaps else None,
        "mapping_rules": Counter(r["mapping_rule"] for r in records).most_common(),
        "records": records,
    }


def export_profile_csv(path: Path, profile_matrix: dict) -> None:
    fieldnames = [
        "bucket_type",
        "bucket_key",
        "rows",
        "unique_emails",
        "sku_token",
        "sku_count",
        "sku_pct",
        "series",
        "series_pct",
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for bucket_type, buckets in profile_matrix["profiles"].items():
            for key, prof in buckets.items():
                if not prof.get("rows"):
                    continue
                sku_counts = prof.get("sku_counts", {})
                sku_pcts = prof.get("sku_pct", {})
                series_pcts = prof.get("series_pct", {})
                if sku_counts:
                    for sku, count in sku_counts.items():
                        writer.writerow(
                            {
                                "bucket_type": bucket_type,
                                "bucket_key": key,
                                "rows": prof["rows"],
                                "unique_emails": prof["unique_emails"],
                                "sku_token": sku,
                                "sku_count": count,
                                "sku_pct": sku_pcts.get(sku, 0),
                                "series": "",
                                "series_pct": "",
                            }
                        )
                for series, sp in series_pcts.items():
                    writer.writerow(
                        {
                            "bucket_type": bucket_type,
                            "bucket_key": key,
                            "rows": prof["rows"],
                            "unique_emails": prof["unique_emails"],
                            "sku_token": "",
                            "sku_count": "",
                            "sku_pct": "",
                            "series": series,
                            "series_pct": sp,
                        }
                    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Full buyer profile GAP with bias correction")
    parser.add_argument("--legacy", type=Path, default=DEFAULT_LEGACY)
    parser.add_argument("--shopify", type=Path, default=DEFAULT_SHOPIFY)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "reports",
    )
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    import os

    engine = create_engine(os.environ["DATABASE_URL"])

    rows = load_buyer_rows(args.legacy, args.shopify)
    profile_matrix = build_profile_matrix(rows)

    buyer_state_counts = Counter(r.state for r in rows if r.state not in ("OTHER",))
    prospect_rec, prospect_states, prospect_by_state_rec = load_prospect_aggregates(engine)
    reweight_table = compute_reweight_table(buyer_state_counts, prospect_states)

    reweight_by_state = {
        r["state"]: r["reweight"]
        for r in reweight_table["by_state"]
        if r.get("reweight") is not None
    }

    raw_buyer_pct = profile_matrix["profiles"]["state_tier"]
    all_sku = Counter(r.sku_token for r in rows)
    raw_buyer_sku_pct = {
        k: round(100.0 * all_sku[k] / len(rows), 2) for k in sorted(all_sku, key=lambda x: -all_sku[x])
    }
    prospect_sku_pct = prospect_token_distribution(prospect_rec)
    reweighted_sku_pct = reweighted_buyer_sku_distribution(rows, reweight_by_state)

    raw_gap = distribution_gap(raw_buyer_sku_pct, prospect_sku_pct)
    reweighted_gap = distribution_gap(reweighted_sku_pct, prospect_sku_pct)
    backlog = calibration_backlog(raw_gap, reweighted_gap)

    prospect_state_gap = build_prospect_state_gap(prospect_by_state_rec, profile_matrix)

    emails = sorted({r.email for r in rows})
    intel_map = load_orion_intel(engine, emails)
    intel_summary = analyze_intel_rows(rows, intel_map)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.output_dir / f"buyer_gap_full_{stamp}.json"
    profile_csv = args.output_dir / f"buyer_profile_matrix_{stamp}.csv"
    reweight_csv = args.output_dir / f"buyer_reweight_table_{stamp}.csv"
    gap_csv = args.output_dir / f"buyer_gap_calibration_{stamp}.csv"

    payload = {
        "generated_at": stamp,
        "methodology": {
            "description": "Buyer profile matrix with geographic reweight (prospect_share/buyer_share)",
            "ca_focus_bias": "Pre-2025 CA sales concentration debiased via state-tier reweight, not CA-only filter",
            "prospect_baseline": "ORION customer_intelligence recommended_product distribution",
            "buyer_universe": "Legacy PAID/PROCESSING + Shopify paid chair line items",
        },
        "universe": {
            "total_buyer_rows": len(rows),
            "unique_buyer_emails": len(emails),
            "orion_matched_emails": len(intel_map),
            "prospect_total": sum(prospect_rec.values()),
        },
        "buyer_profile_matrix": profile_matrix,
        "reweight_table": reweight_table,
        "aggregate_gap": {
            "raw_buyer_sku_pct": raw_buyer_sku_pct,
            "reweighted_buyer_sku_pct": reweighted_sku_pct,
            "prospect_recommended_sku_pct": prospect_sku_pct,
            "raw_distribution_gap": raw_gap,
            "reweighted_distribution_gap": reweighted_gap,
        },
        "calibration_backlog": backlog,
        "prospect_state_gap": prospect_state_gap,
        "intel_matched_rule_gap": {
            k: v for k, v in intel_summary.items() if k != "records"
        },
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    export_profile_csv(profile_csv, profile_matrix)

    with open(reweight_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=reweight_table["by_state"][0].keys())
        writer.writeheader()
        writer.writerows(reweight_table["by_state"])

    with open(gap_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "sku",
                "raw_buyer_pct",
                "raw_prospect_pct",
                "raw_gap_points",
                "reweighted_buyer_pct",
                "reweighted_gap_points",
                "bias_effect_pp",
                "suggested_action",
            ],
        )
        writer.writeheader()
        writer.writerows(backlog)

    print(
        json.dumps(
            {
                "json": str(json_path),
                "profile_csv": str(profile_csv),
                "reweight_csv": str(reweight_csv),
                "gap_csv": str(gap_csv),
                "summary": {
                    "buyer_rows": len(rows),
                    "ca_tier_reweight": reweight_table["by_state_tier"]["CA"]["reweight"],
                    "raw_gap_top3": sorted(raw_gap.items(), key=lambda x: -abs(x[1]["gap_points"]))[:3],
                    "reweighted_gap_top3": sorted(
                        reweighted_gap.items(), key=lambda x: -abs(x[1]["gap_points"])
                    )[:3],
                    "calibration_backlog": backlog[:5],
                    "intel_matched": intel_summary.get("intel_matched_rows"),
                },
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
