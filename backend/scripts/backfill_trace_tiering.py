#!/usr/bin/env python3
"""Backfill legacy customer_intelligence.trace_json into intelligence_trace (Phase 1)."""

from __future__ import annotations

import argparse
import os
import sys
import uuid

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from app.database import SessionLocal  # noqa: E402
from app.intelligence.trace_backfill import (  # noqa: E402
    backfill_legacy_traces,
    count_legacy_inline_rows,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill tiered intelligence trace storage")
    parser.add_argument("--dry-run", action="store_true", help="Count and simulate without writing")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--commit-every", type=int, default=1000)
    parser.add_argument("--upload-id", type=str, default=None, help="Limit backfill to one upload UUID")
    parser.add_argument("--vacuum", action="store_true", help="Run SQLite VACUUM after backfill")
    args = parser.parse_args()

    upload_id = uuid.UUID(args.upload_id) if args.upload_id else None
    db = SessionLocal()
    try:
        before = count_legacy_inline_rows(db)
        print(f"Legacy inline rows: {before}")
        if before == 0:
            print("Nothing to backfill.")
            if not args.vacuum:
                return 0
        else:
            stats = backfill_legacy_traces(
                db,
                batch_size=args.batch_size,
                commit_every=args.commit_every,
                dry_run=args.dry_run,
                upload_id=upload_id,
            )
            after = count_legacy_inline_rows(db) if not args.dry_run else before

            print("Backfill stats:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            if not args.dry_run:
                print(f"Remaining legacy inline rows: {after}")

            if stats.get("errors"):
                return 1

        if args.vacuum and not args.dry_run:
            from sqlalchemy import text

            from app.database import engine

            if engine.dialect.name == "sqlite":
                print("Running VACUUM to reclaim SQLite space (may take several minutes)...")
                with engine.connect() as conn:
                    conn.execution_options(isolation_level="AUTOCOMMIT").execute(text("VACUUM"))
                print("VACUUM complete.")
            else:
                print("VACUUM skipped (not SQLite).")

        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
