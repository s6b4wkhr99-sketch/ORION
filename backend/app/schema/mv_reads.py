"""Read Volume 16 materialized views when available."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine


def _is_postgres() -> bool:
    dialect = engine.url.get_driver_name()
    return dialect.startswith("postgresql") or dialect.startswith("psycopg2")


def read_mv_state_revenue(db: Session) -> list[dict] | None:
    if not _is_postgres():
        return None
    try:
        rows = db.execute(
            text(
                """
                SELECT state, customer_count, total_expected_revenue
                FROM mv_state_revenue
                WHERE state IS NOT NULL
                ORDER BY total_expected_revenue DESC NULLS LAST
                """
            )
        ).fetchall()
    except Exception:
        return None
    if not rows:
        return None
    return [
        {
            "state": state or "Unknown",
            "customers": int(count or 0),
            "revenue": round(float(revenue or 0), 2),
            "orders": 0.0,
            "conversion": 0.0,
        }
        for state, count, revenue in rows
    ]


def read_mv_product_performance(db: Session) -> list[dict] | None:
    if not _is_postgres():
        return None
    try:
        rows = db.execute(
            text(
                """
                SELECT recommended_product, customer_count, total_expected_revenue
                FROM mv_product_performance
                WHERE recommended_product IS NOT NULL
                ORDER BY total_expected_revenue DESC NULLS LAST
                """
            )
        ).fetchall()
    except Exception:
        return None
    if not rows:
        return None
    total_revenue = sum(float(revenue or 0) for _, _, revenue in rows)
    return [
        {
            "product": product or "Unknown",
            "customers": int(count or 0),
            "revenue": round(float(revenue or 0), 2),
            "share_pct": round((float(revenue or 0) / total_revenue * 100) if total_revenue else 0, 1),
        }
        for product, count, revenue in rows
    ]


def refresh_dashboard_materialized_views() -> None:
    if not _is_postgres():
        return
    from app.schema.apply import refresh_materialized_views

    refresh_materialized_views(engine)
