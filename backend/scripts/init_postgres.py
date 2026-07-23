#!/usr/bin/env python3
"""Initialize PostgreSQL for CIOS (migrations, physical schema, seeds, verification)."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.database import Base, SessionLocal, is_postgres_url
import app.models  # noqa: F401 — register all ORM mappers before SessionLocal
from app.processing.seed import seed_configuration
from app.schema.apply import apply_physical_schema
from app.schema.seed_v16 import seed_v16_reference_schema
from app.security.users import seed_users


def wait_for_postgres(url: str, attempts: int = 30, delay: float = 2.0) -> None:
    engine = create_engine(url, pool_pre_ping=True)
    for attempt in range(1, attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"PostgreSQL connection OK (attempt {attempt})")
            return
        except OperationalError as exc:
            if attempt == attempts:
                raise SystemExit(f"PostgreSQL not reachable after {attempts} attempts: {exc}") from exc
            print(f"Waiting for PostgreSQL... ({attempt}/{attempts})")
            time.sleep(delay)


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize CIOS PostgreSQL database")
    parser.add_argument("--verify-only", action="store_true", help="Only verify connectivity and table count")
    args = parser.parse_args()

    url = settings.database_url
    if not is_postgres_url(url):
        print(f"ERROR: DATABASE_URL is not PostgreSQL: {url}")
        print("Set DATABASE_URL=postgresql+psycopg2://cios:cios_dev_password@127.0.0.1:5432/cios")
        return 1

    wait_for_postgres(url)
    engine = create_engine(url, pool_pre_ping=True, pool_size=settings.database_pool_size)

    if args.verify_only:
        with engine.connect() as conn:
            count = conn.execute(
                text("SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public'")
            ).scalar()
        print(f"VERIFY OK — {count} public tables")
        return 0

    Base.metadata.create_all(bind=engine)
    apply_physical_schema(engine)

    db = SessionLocal()
    try:
        seed_configuration(db)
        seed_users(db)
        seed_v16_reference_schema(db)
    finally:
        db.close()

    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
        tables = conn.execute(
            text("SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public'")
        ).scalar()

    print(f"INIT OK — PostgreSQL {str(version).split(',')[0]}")
    print(f"         {tables} public tables, bulk_mode={settings.bulk_upload_mode}, async={settings.upload_async}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
