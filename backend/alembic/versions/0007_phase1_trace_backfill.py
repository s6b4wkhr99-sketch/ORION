"""Phase 1 — Backfill legacy inline traces into intelligence_trace (optional / batched)."""

import logging

from alembic import op

revision = "0007_phase1_trace_backfill"
down_revision = "0006_phase1_scale"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    from app.intelligence.trace_backfill import run_backfill_for_upgrade

    connection = op.get_bind()
    stats = run_backfill_for_upgrade(connection)
    if stats.get("deferred"):
        logger.warning(stats.get("message", "Trace backfill deferred — run scripts/backfill_trace_tiering.py"))
    elif stats.get("skipped") and stats.get("candidates", 0) > 0:
        logger.info(
            "Trace backfill skipped (%s legacy rows). Set RUN_TRACE_BACKFILL=1 or run scripts/backfill_trace_tiering.py",
            stats["candidates"],
        )
    elif stats.get("processed"):
        logger.info(
            "Trace backfill complete: processed=%s inline_cleared=%s errors=%s",
            stats.get("processed"),
            stats.get("inline_cleared"),
            stats.get("errors"),
        )


def downgrade() -> None:
    # Data migration is not reversed — inline blobs were nulled after copy to intelligence_trace.
    pass
