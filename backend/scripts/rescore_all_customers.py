#!/usr/bin/env python3
"""Re-score customers through the intelligence pipeline using the CURRENT ZIP income reference
and product-ladder recommendation rules, then rebuild that upload's rollups.

DB-only and faithful: process_upload feeds the pipeline the exact same datalogix dict it stores in
customer_datalogix, so reconstructing datalogix_raw from those columns reproduces upload scoring.
Normalization is skipped (customer state/zip/city already normalized in the DB).

Usage:
  python scripts/rescore_all_customers.py                 # full run (all uploads) + cache invalidate
  python scripts/rescore_all_customers.py --state CA      # only customers in a state (test)
  python scripts/rescore_all_customers.py --limit 5000    # cap scored customers (test)
  python scripts/rescore_all_customers.py --no-rollups    # skip rollup rebuild
  python scripts/rescore_all_customers.py --rollups-only  # only rebuild rollups + invalidate cache
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from sqlalchemy import text  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.customer import Customer, CustomerDatalogix  # noqa: E402
from app.models.raw import RawUpload  # noqa: E402
from app.acquisition.upload import _load_zip_cache, _get_zip_ref  # noqa: E402
from app.acquisition.rollup import build_upload_rollup  # noqa: E402
from app.intelligence.pipeline import run_intelligence_pipeline  # noqa: E402
from app.intelligence.trace_storage import persist_intelligence_result  # noqa: E402
from app.cache.dashboard_cache import invalidate_dashboard_cache  # noqa: E402

# customer_datalogix columns == the datalogix_raw keys the pipeline consumes at upload time.
DL_COLS = [
    "age_range", "generation", "gender", "estimated_income", "home_value", "household",
    "length_of_residence", "net_worth", "online_access", "retail_card", "dwelling",
    "bank_card", "adults", "children", "persons", "dma_code", "county_code",
]

# Smaller chunks + commit-per-chunk reduce deadlock windows against concurrent AccessExclusiveLock.
CHUNK = 1000
MAX_DEADLOCK_RETRIES = 15
GENERATED_BY = "rescore_sku_migration_s4_v1"


def _is_deadlock(exc: BaseException) -> bool:
    text = str(exc).lower()
    return (
        "deadlock" in text
        or "lock_timeout" in text
        or "lock timeout" in text
        or "locknotavailable" in text
        or "could not serialize" in text
    )


def _with_deadlock_retry(db, label: str, fn, *, max_retries: int = MAX_DEADLOCK_RETRIES):
    """Run fn(); on deadlock/lock timeout roll back and retry with backoff."""
    for attempt in range(1, max_retries + 1):
        try:
            result = fn()
            db.commit()
            return result
        except OperationalError as exc:
            db.rollback()
            if not _is_deadlock(exc) or attempt >= max_retries:
                raise
            delay = min(30.0, (0.4 * (2 ** (attempt - 1))) + random.uniform(0, 0.35))
            print(
                f"  deadlock/lock on {label} (attempt {attempt}/{max_retries}); "
                f"retry in {delay:.1f}s",
                flush=True,
            )
            time.sleep(delay)
    raise RuntimeError(f"unreachable retry loop for {label}")


def _rescore_chunk(db, zip_cache, customer_ids) -> int:
    rows = (
        db.query(Customer, CustomerDatalogix)
        .join(CustomerDatalogix, CustomerDatalogix.customer_id == Customer.customer_id)
        .filter(Customer.customer_id.in_(customer_ids))
        .all()
    )
    for cust, dl in rows:
        datalogix_raw = {c: getattr(dl, c) for c in DL_COLS}
        ctx = run_intelligence_pipeline(
            customer={"email": cust.email, "state": cust.state, "zip": cust.zip, "city": cust.city},
            datalogix_raw=datalogix_raw,
            zip_lookup=lambda z: _get_zip_ref(db, z, zip_cache),
            zip_ref=_get_zip_ref(db, cust.zip, zip_cache),
        )
        persist_intelligence_result(
            db,
            cust,
            ctx.to_intelligence_dict(),
            store_full_trace=False,
            record_versions=False,
            sync_recommendation=False,
            generated_by=GENERATED_BY,
        )
    return len(rows)


def rescore(db, *, state: str | None, limit: int | None, do_rollups: bool) -> None:
    # Prefer aborting waiters quickly so the rescore can retry instead of hanging.
    for stmt in ("SET lock_timeout = '120s'", "SET statement_timeout = '300s'"):
        try:
            db.execute(text(stmt))
            db.commit()
        except Exception as exc:  # noqa: BLE001 — sqlite / restricted roles
            db.rollback()
            print(f"Note: could not apply {stmt} ({exc})", flush=True)

    zip_cache = _load_zip_cache(db)
    print(f"Loaded zip cache: {len(zip_cache):,} ZIPs", flush=True)

    uploads = [u.upload_id for u in db.query(RawUpload.upload_id).all()]
    print(f"Uploads to process: {len(uploads)}", flush=True)
    print(f"Chunk size={CHUNK:,} · deadlock retries={MAX_DEADLOCK_RETRIES}", flush=True)

    total_scored = 0
    t0 = time.time()
    for idx, uid in enumerate(uploads, start=1):
        id_q = db.query(Customer.customer_id).filter(Customer.upload_id == uid)
        if state:
            id_q = id_q.filter(Customer.state == state)
        ids = [r[0] for r in id_q.all()]
        if not ids:
            continue

        upload_scored = 0
        for start in range(0, len(ids), CHUNK):
            chunk = ids[start:start + CHUNK]

            def _run_chunk(chunk_ids=chunk):
                return _rescore_chunk(db, zip_cache, chunk_ids)

            scored = _with_deadlock_retry(db, f"chunk upload={str(uid)[:8]}@{start}", _run_chunk)
            upload_scored += scored
            total_scored += scored
            if limit and total_scored >= limit:
                break

        if do_rollups and upload_scored:
            def _run_rollup(upload_id=uid):
                build_upload_rollup(db, upload_id)
                return True

            _with_deadlock_retry(db, f"rollup upload={str(uid)[:8]}", _run_rollup)

        rate = total_scored / max(time.time() - t0, 1e-6)
        print(
            f"[{idx}/{len(uploads)}] upload={str(uid)[:8]} scored={upload_scored:,} "
            f"| total={total_scored:,} | {rate:,.0f}/s | rollups={'yes' if do_rollups and upload_scored else 'no'}",
            flush=True,
        )
        if limit and total_scored >= limit:
            print("Reached --limit; stopping.", flush=True)
            break

    print(f"Re-scored {total_scored:,} customers in {time.time() - t0:,.0f}s", flush=True)


def rebuild_all_rollups(db) -> None:
    uploads = [u.upload_id for u in db.query(RawUpload.upload_id).all()]
    t0 = time.time()
    for idx, uid in enumerate(uploads, start=1):
        def _run_rollup(upload_id=uid):
            build_upload_rollup(db, upload_id)
            return True

        _with_deadlock_retry(db, f"rollup upload={str(uid)[:8]}", _run_rollup)
        print(f"[{idx}/{len(uploads)}] rebuilt rollups for {str(uid)[:8]}", flush=True)
    print(f"Rebuilt rollups for {len(uploads)} uploads in {time.time() - t0:,.0f}s", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-score customers + rebuild rollups")
    parser.add_argument("--state", default=None, help="Only re-score customers in this state")
    parser.add_argument("--limit", type=int, default=None, help="Cap number of customers scored")
    parser.add_argument("--no-rollups", action="store_true", help="Skip rollup rebuild")
    parser.add_argument("--rollups-only", action="store_true", help="Only rebuild rollups + cache")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.rollups_only:
            rebuild_all_rollups(db)
        else:
            rescore(db, state=args.state, limit=args.limit, do_rollups=not args.no_rollups)
        invalidate_dashboard_cache()
        print("Dashboard cache invalidated. Done.", flush=True)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
