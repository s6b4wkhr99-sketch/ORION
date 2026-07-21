#!/usr/bin/env python3
"""Compact duplicate rationale JSON in customer_intelligence and recommendation tables."""

from __future__ import annotations

import argparse
import json
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from sqlalchemy import text

from app.database import SessionLocal
from app.models.customer import CustomerIntelligence
from app.models.v16_schema import Recommendation


def compact_framework_summary(summary: dict) -> tuple[dict, bool]:
    if not summary.get("recommendation_rationale"):
        return summary, False
    categories = summary.get("categories")
    if not isinstance(categories, dict):
        return summary, False
    recommendation = categories.get("recommendation")
    if not isinstance(recommendation, dict) or "rationale" not in recommendation:
        return summary, False
    compact = dict(summary)
    compact_categories = dict(categories)
    compact_rec = dict(recommendation)
    compact_rec.pop("rationale", None)
    compact_categories["recommendation"] = compact_rec
    compact["categories"] = compact_categories
    return compact, True


def compact_audit_json(audit: dict) -> tuple[dict, bool]:
    if "recommendation_rationale" not in audit:
        return audit, False
    compact = dict(audit)
    compact.pop("recommendation_rationale", None)
    return compact, True


def compact_framework_rows(
    db,
    *,
    batch_size: int,
    commit_every: int,
    dry_run: bool,
) -> dict[str, int]:
    stats = {"processed": 0, "compacted": 0, "skipped": 0, "errors": 0}
    pending = 0
    last_id = None

    while True:
        batch_query = (
            db.query(CustomerIntelligence.customer_id, CustomerIntelligence.framework_summary_json)
            .filter(CustomerIntelligence.framework_summary_json.isnot(None))
            .order_by(CustomerIntelligence.customer_id)
        )
        if last_id is not None:
            batch_query = batch_query.filter(CustomerIntelligence.customer_id > last_id)
        rows = batch_query.limit(batch_size).all()
        if not rows:
            break

        for customer_id, raw_json in rows:
            stats["processed"] += 1
            try:
                summary = json.loads(raw_json)
            except json.JSONDecodeError:
                stats["errors"] += 1
                continue

            compact, changed = compact_framework_summary(summary)
            if not changed:
                stats["skipped"] += 1
                continue

            stats["compacted"] += 1
            if dry_run:
                continue

            db.query(CustomerIntelligence).filter(CustomerIntelligence.customer_id == customer_id).update(
                {"framework_summary_json": json.dumps(compact, separators=(",", ":"))},
                synchronize_session=False,
            )
            pending += 1
            if pending >= commit_every:
                db.commit()
                pending = 0
                if stats["processed"] % 100000 == 0:
                    print(f"framework_summary progress: processed={stats['processed']:,} compacted={stats['compacted']:,}")

        last_id = rows[-1][0]
        if not dry_run:
            db.commit()
            pending = 0

    if not dry_run and pending:
        db.commit()
    return stats


def compact_recommendation_rows(
    db,
    *,
    batch_size: int,
    commit_every: int,
    dry_run: bool,
) -> dict[str, int]:
    stats = {"processed": 0, "compacted": 0, "skipped": 0, "errors": 0}
    pending = 0
    last_id = None

    while True:
        batch_query = (
            db.query(Recommendation.recommendation_id, Recommendation.audit_json)
            .filter(Recommendation.audit_json.isnot(None))
            .order_by(Recommendation.recommendation_id)
        )
        if last_id is not None:
            batch_query = batch_query.filter(Recommendation.recommendation_id > last_id)
        rows = batch_query.limit(batch_size).all()
        if not rows:
            break

        for recommendation_id, raw_json in rows:
            stats["processed"] += 1
            try:
                audit = json.loads(raw_json)
            except json.JSONDecodeError:
                stats["errors"] += 1
                continue

            compact, changed = compact_audit_json(audit)
            if not changed:
                stats["skipped"] += 1
                continue

            stats["compacted"] += 1
            if dry_run:
                continue

            db.query(Recommendation).filter(Recommendation.recommendation_id == recommendation_id).update(
                {"audit_json": json.dumps(compact, separators=(",", ":"))},
                synchronize_session=False,
            )
            pending += 1
            if pending >= commit_every:
                db.commit()
                pending = 0
                if stats["processed"] % 100000 == 0:
                    print(f"recommendation progress: processed={stats['processed']:,} compacted={stats['compacted']:,}")

        last_id = rows[-1][0]
        if not dry_run:
            db.commit()
            pending = 0

    if not dry_run and pending:
        db.commit()
    return stats


def run_vacuum_full(tables: list[str]) -> None:
    db = SessionLocal()
    try:
        db.commit()
        conn = db.connection().connection
        conn.set_isolation_level(0)
        cur = conn.cursor()
        for table in tables:
            print(f"Running VACUUM FULL {table} ...")
            cur.execute(f"VACUUM FULL {table}")
        cur.close()
    finally:
        db.close()


def print_sizes(label: str) -> None:
    db = SessionLocal()
    try:
        db_size = db.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))")).scalar()
        ci = db.execute(
            text("SELECT pg_size_pretty(pg_total_relation_size('customer_intelligence'::regclass))")
        ).scalar()
        rec = db.execute(text("SELECT pg_size_pretty(pg_total_relation_size('recommendation'::regclass))")).scalar()
        print(f"{label}: db={db_size} customer_intelligence={ci} recommendation={rec}")
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compact duplicate rationale JSON storage")
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--commit-every", type=int, default=10000)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-recommendation", action="store_true")
    parser.add_argument("--vacuum-full", action="store_true")
    args = parser.parse_args()

    print_sizes("Before")
    db = SessionLocal()
    try:
        fw_stats = compact_framework_rows(
            db,
            batch_size=args.batch_size,
            commit_every=args.commit_every,
            dry_run=args.dry_run,
        )
        print("framework_summary:", fw_stats)

        if not args.skip_recommendation:
            rec_stats = compact_recommendation_rows(
                db,
                batch_size=args.batch_size,
                commit_every=args.commit_every,
                dry_run=args.dry_run,
            )
            print("recommendation audit:", rec_stats)
    finally:
        db.close()

    if args.vacuum_full and not args.dry_run:
        tables = ["customer_intelligence"]
        if not args.skip_recommendation:
            tables.append("recommendation")
        run_vacuum_full(tables)

    print_sizes("After")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
