"""Volume 16 — Apply indexes, views, and PostgreSQL objects."""

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.schema.views import INDEX_DDL, MATERIALIZED_VIEW_DDL, VIEW_DDL

logger = logging.getLogger("cios.schema")


def _is_postgres(engine: Engine) -> bool:
    dialect = engine.url.get_driver_name()
    return dialect.startswith("postgresql") or dialect.startswith("psycopg2")


def apply_physical_schema(engine: Engine) -> None:
    """Create Volume 16 indexes and views (PostgreSQL materialized views when supported)."""
    with engine.begin() as conn:
        for ddl in INDEX_DDL:
            try:
                conn.execute(text(ddl))
            except Exception as exc:
                logger.debug("Index skipped: %s", exc)

        for name, ddl in VIEW_DDL.items():
            try:
                conn.execute(text(ddl))
            except Exception as exc:
                logger.warning("View %s skipped: %s", name, exc)

        if _is_postgres(engine):
            for name, ddl in MATERIALIZED_VIEW_DDL.items():
                try:
                    conn.execute(text(ddl))
                except Exception as exc:
                    logger.warning("Materialized view %s skipped: %s", name, exc)
            _apply_postgres_checks(conn)


def refresh_materialized_views(engine: Engine) -> None:
    if not _is_postgres(engine):
        return
    with engine.begin() as conn:
        for name in MATERIALIZED_VIEW_DDL:
            try:
                conn.execute(text(f"REFRESH MATERIALIZED VIEW {name}"))
            except Exception as exc:
                logger.debug("MV refresh %s: %s", name, exc)


def _apply_postgres_checks(conn) -> None:
    checks = [
        (
            "customer_intelligence",
            "chk_expected_conversion_range",
            "expected_conversion >= 0 AND expected_conversion <= 1",
        ),
        ("customer_intelligence", "chk_expected_revenue_nonneg", "expected_revenue >= 0"),
        ("campaign", "chk_forecast_revenue_nonneg", "forecast_revenue IS NULL OR forecast_revenue >= 0"),
        ("campaign", "chk_actual_revenue_nonneg", "actual_revenue IS NULL OR actual_revenue >= 0"),
    ]
    for table, name, expr in checks:
        try:
            conn.execute(text(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {name}"))
            conn.execute(text(f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({expr})"))
        except Exception as exc:
            logger.debug("Check constraint %s: %s", name, exc)
