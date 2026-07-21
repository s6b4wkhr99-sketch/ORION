"""Phase 1 — Backfill legacy inline trace_json into tiered intelligence_trace storage."""

from __future__ import annotations

import json
import os
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.intelligence.trace_storage import build_framework_summary, build_trace_summary
from app.models.customer import Customer, CustomerIntelligence
from app.models.scale import IntelligenceTrace

DEFAULT_BATCH_SIZE = 500
DEFAULT_COMMIT_EVERY = 1000


def count_legacy_inline_rows(db: Session) -> int:
    """Rows still storing full trace/framework inline on customer_intelligence."""
    return (
        db.query(CustomerIntelligence)
        .filter(
            or_(
                CustomerIntelligence.trace_json.isnot(None),
                CustomerIntelligence.framework_json.isnot(None),
            )
        )
        .count()
    )


def _parse_trace(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _parse_framework(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _upsert_trace_row(
    db: Session,
    customer_id,
    trace_json: str,
    framework_json: str,
    existing: IntelligenceTrace | None,
) -> IntelligenceTrace:
    if existing:
        existing.trace_json = trace_json
        existing.framework_json = framework_json
        return existing
    row = IntelligenceTrace(
        customer_id=customer_id,
        trace_json=trace_json,
        framework_json=framework_json,
    )
    db.add(row)
    return row


def backfill_legacy_traces(
    db: Session,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    commit_every: int = DEFAULT_COMMIT_EVERY,
    dry_run: bool = False,
    upload_id=None,
    auto_commit: bool = True,
) -> dict[str, int]:
    """
    Move inline trace_json/framework_json to intelligence_trace and populate summaries.

    Idempotent: only processes rows where inline trace or framework is still present.
    """
    query = db.query(CustomerIntelligence).filter(
        or_(
            CustomerIntelligence.trace_json.isnot(None),
            CustomerIntelligence.framework_json.isnot(None),
        )
    )
    if upload_id is not None:
        query = query.join(Customer, Customer.customer_id == CustomerIntelligence.customer_id).filter(
            Customer.upload_id == upload_id
        )

    stats = {
        "candidates": query.count(),
        "processed": 0,
        "trace_rows_upserted": 0,
        "summaries_built": 0,
        "inline_cleared": 0,
        "skipped_empty": 0,
        "errors": 0,
    }
    if stats["candidates"] == 0:
        return stats

    pending_commit = 0
    for intel in query.yield_per(batch_size):
        inline_trace = intel.trace_json
        inline_framework = intel.framework_json
        if not inline_trace and not inline_framework:
            stats["skipped_empty"] += 1
            continue

        rule_trace = _parse_trace(inline_trace)
        framework = _parse_framework(inline_framework)
        trace_payload = inline_trace if inline_trace else json.dumps(rule_trace)
        framework_payload = inline_framework if inline_framework else json.dumps(framework)

        if dry_run:
            stats["processed"] += 1
            if inline_trace or inline_framework:
                stats["inline_cleared"] += 1
            continue

        try:
            trace_row = (
                db.query(IntelligenceTrace)
                .filter(IntelligenceTrace.customer_id == intel.customer_id)
                .first()
            )
            _upsert_trace_row(db, intel.customer_id, trace_payload, framework_payload, trace_row)
            stats["trace_rows_upserted"] += 1

            if not intel.trace_summary_json:
                intel.trace_summary_json = json.dumps(build_trace_summary(rule_trace, framework))
                stats["summaries_built"] += 1
            if not intel.framework_summary_json:
                intel.framework_summary_json = json.dumps(build_framework_summary(framework))
                stats["summaries_built"] += 1

            intel.trace_json = None
            intel.framework_json = None
            stats["inline_cleared"] += 1
            stats["processed"] += 1
            pending_commit += 1

            if auto_commit and commit_every > 0 and pending_commit >= commit_every:
                db.commit()
                pending_commit = 0
        except Exception:
            if auto_commit:
                db.rollback()
            stats["errors"] += 1
            pending_commit = 0

    if not dry_run and auto_commit and pending_commit:
        db.commit()

    return stats


def should_run_backfill_on_upgrade() -> bool:
    """Skip heavy backfill during alembic upgrade unless explicitly enabled."""
    if os.environ.get("SKIP_TRACE_BACKFILL", "").strip().lower() in {"1", "true", "yes"}:
        return False
    if os.environ.get("RUN_TRACE_BACKFILL", "").strip().lower() in {"1", "true", "yes"}:
        return True
    # Default: auto-run only for small legacy sets (fresh CI / dev seeds).
    return True


def run_backfill_for_upgrade(connection) -> dict[str, int]:
    """Entry point for Alembic 0007 — uses connection-bound session."""
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=connection)
    db = SessionLocal()
    try:
        legacy_count = count_legacy_inline_rows(db)
        if legacy_count == 0:
            return {"candidates": 0, "processed": 0, "skipped": 1}

        if not should_run_backfill_on_upgrade():
            return {"candidates": legacy_count, "processed": 0, "skipped": 1}

        auto_limit = int(os.environ.get("TRACE_BACKFILL_AUTO_LIMIT", "5000"))
        if legacy_count > auto_limit and os.environ.get("RUN_TRACE_BACKFILL", "").strip().lower() not in {
            "1",
            "true",
            "yes",
        }:
            return {
                "candidates": legacy_count,
                "processed": 0,
                "skipped": 1,
                "deferred": 1,
                "message": (
                    f"Legacy rows ({legacy_count}) exceed auto limit ({auto_limit}). "
                    "Run: python scripts/backfill_trace_tiering.py"
                ),
            }

        return backfill_legacy_traces(
            db,
            batch_size=DEFAULT_BATCH_SIZE,
            commit_every=DEFAULT_COMMIT_EVERY,
            auto_commit=False,
        )
    finally:
        db.close()
