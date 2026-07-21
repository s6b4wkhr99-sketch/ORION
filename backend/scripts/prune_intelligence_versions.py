#!/usr/bin/env python3
"""Prune intelligence_version history and reclaim PostgreSQL disk space."""

from __future__ import annotations

import argparse
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from sqlalchemy import text

from app.database import SessionLocal


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune intelligence version history")
    parser.add_argument(
        "--keep-per-customer",
        type=int,
        default=1,
        help="Number of latest versions to retain per customer (default: 1)",
    )
    parser.add_argument("--vacuum", action="store_true", help="Run VACUUM ANALYZE after delete")
    parser.add_argument(
        "--vacuum-full",
        action="store_true",
        help="Run VACUUM FULL to return disk to OS (slower, brief table lock)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report counts only")
    args = parser.parse_args()
    keep = max(1, args.keep_per_customer)

    db = SessionLocal()
    try:
        before = db.execute(text("SELECT COUNT(*) FROM intelligence_version")).scalar()
        db_size_before = db.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))")).scalar()
        ver_size_before = db.execute(
            text(
                "SELECT pg_size_pretty(pg_total_relation_size('intelligence_version'::regclass))"
            )
        ).scalar()

        print(f"Before: versions={before:,} db={db_size_before} intelligence_version={ver_size_before}")

        if args.dry_run:
            to_delete = db.execute(
                text(
                    """
                    SELECT COUNT(*) FROM intelligence_version iv
                    WHERE iv.version <= (
                        SELECT MAX(v2.version) - :keep
                        FROM intelligence_version v2
                        WHERE v2.customer_id = iv.customer_id
                    )
                    """
                ),
                {"keep": keep},
            ).scalar()
            print(f"Would delete: {to_delete:,} rows (keeping {keep} per customer)")
            return 0

        # Delete older versions, keep N latest per customer.
        result = db.execute(
            text(
                """
                DELETE FROM intelligence_version iv
                WHERE iv.version <= (
                    SELECT MAX(v2.version) - :keep
                    FROM intelligence_version v2
                    WHERE v2.customer_id = iv.customer_id
                )
                """
            ),
            {"keep": keep},
        )
        db.commit()
        deleted = result.rowcount or 0
        print(f"Deleted: {deleted:,} version rows")

        after = db.execute(text("SELECT COUNT(*) FROM intelligence_version")).scalar()
        ver_size_after = db.execute(
            text(
                "SELECT pg_size_pretty(pg_total_relation_size('intelligence_version'::regclass))"
            )
        ).scalar()
        db_size_after = db.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))")).scalar()
        print(f"After: versions={after:,} db={db_size_after} intelligence_version={ver_size_after}")

        if args.vacuum or args.vacuum_full:
            # VACUUM cannot run inside a transaction block.
            db.commit()
            conn = db.connection().connection
            conn.set_isolation_level(0)
            cur = conn.cursor()
            cmd = "VACUUM FULL" if args.vacuum_full else "VACUUM ANALYZE"
            print(f"Running {cmd} intelligence_version ...")
            cur.execute(f"{cmd} intelligence_version")
            if not args.vacuum_full:
                cur.execute("VACUUM ANALYZE customer_intelligence")
            cur.close()
            db_size_final = db.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))")).scalar()
            ver_size_final = db.execute(
                text(
                    "SELECT pg_size_pretty(pg_total_relation_size('intelligence_version'::regclass))"
                )
            ).scalar()
            print(f"Post-vacuum db size: {db_size_final} intelligence_version: {ver_size_final}")

        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
