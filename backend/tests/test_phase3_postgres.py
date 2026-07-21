"""Phase 3 — PostgreSQL connectivity and schema acceptance (optional CI/local)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

from app.database import is_postgres_url


def run_tests() -> int:
    database_url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
    if not is_postgres_url(database_url):
        print("SKIP Phase 3 PostgreSQL tests — set TEST_DATABASE_URL or DATABASE_URL to postgresql+psycopg2://...")
        return 0

    passed = 0
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
        assert "PostgreSQL" in version
        print(f"✓ PostgreSQL connected ({version.split(',')[0]})")
        passed += 1

        tables = conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        ).fetchall()
        assert tables, "No public tables — run alembic upgrade head"
        print(f"✓ PostgreSQL schema present ({len(tables)} tables)")
        passed += 1

    from app.schema.apply import apply_physical_schema

    apply_physical_schema(engine)
    print("✓ apply_physical_schema succeeds on PostgreSQL")
    passed += 1

    print(f"\nPhase 3 PostgreSQL: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
