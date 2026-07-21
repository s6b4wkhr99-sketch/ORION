"""Volume 16 Section 15 — Physical schema acceptance tests."""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text

from fastapi.testclient import TestClient

from app.schema.registry import (
    CHECK_CONSTRAINTS,
    FOREIGN_KEYS,
    INDEXES,
    MATERIALIZED_VIEWS,
    SPEC_TABLES,
    TABLE_MAP,
    TRIGGERS,
    VIEWS,
)
from app.database import engine
from app.schema.views import VIEW_DDL
from app.main import app
from app.models.v16_schema import ProviderFieldMapping, ProviderMaster, UploadHistory
from app.models.customer import CustomerIntelligence
from app.models.v16_schema import Recommendation
from app.database import Base, SessionLocal
from app.processing.seed import seed_configuration
from app.schema.seed_v16 import seed_v16_reference_schema
from app.security.users import seed_users


BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_ROOT)


def _reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.schema.apply import apply_physical_schema

    apply_physical_schema(engine)
    db = SessionLocal()
    seed_configuration(db)
    seed_users(db)
    seed_v16_reference_schema(db)
    db.close()


def run_tests():
    _reset()
    passed = 0
    inspector = inspect(engine)

    # DB-001 — spec tables mapped to physical implementation
    for spec_table in SPEC_TABLES:
        physical = TABLE_MAP[spec_table]
        assert physical in inspector.get_table_names(), physical
    print("✓ DB-001 Single source of truth — all spec tables mapped")
    passed += 1

    # Section 5 supplemental tables exist
    for table in (
        "upload_history",
        "campaign_target",
        "campaign_report",
        "recommendation",
        "provider",
        "provider_field_mapping",
        "role",
        "permission",
    ):
        assert table in inspector.get_table_names()
    print("✓ Section 5–6 Table specifications materialized")
    passed += 1

    # Section 7 — foreign keys on ORM models
    assert len(FOREIGN_KEYS) >= 8
    print("✓ Section 7 Foreign key registry documented")
    passed += 1

    # Section 8 — indexes applied
    customer_indexes = {idx["name"] for idx in inspector.get_indexes("customers")}
    assert "idx_customer_email" in customer_indexes or "ix_customers_email" in customer_indexes
    print("✓ Section 8 Index strategy")
    passed += 1

    # Section 9 — constraints registry
    assert any(c[0] == "customer_intelligence" for c in CHECK_CONSTRAINTS)
    print("✓ Section 9 Constraints documented")
    passed += 1

    # Section 10 — views
    with engine.connect() as conn:
        for view in VIEWS:
            conn.execute(text(f"SELECT 1 FROM {view} LIMIT 1"))
    assert len(VIEW_DDL) == len(VIEWS)
    print("✓ Section 10 Database views")
    passed += 1

    # Section 11 — materialized views registry
    assert len(MATERIALIZED_VIEWS) == 3
    print("✓ Section 11 Materialized views documented")
    passed += 1

    # Section 12 — trigger behaviors
    client = TestClient(app)
    r = client.post("/api/v1/auth/login", json={"email": "user@company.com", "password": "Ceragem2026!Adm"})
    headers = {"Authorization": f"Bearer {r.json()['data']['token']}"}
    sample = "Email,First Name,Last Name,State,ZIP\nv16@test.com,V16,User,CT,06801\n"
    r = client.post(
        "/api/v1/customers/upload",
        files={"file": ("v16.csv", io.BytesIO(sample.encode()), "text/csv")},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    db = SessionLocal()
    assert db.query(UploadHistory).count() >= 1
    assert db.query(Recommendation).count() >= 1
    intel = db.query(CustomerIntelligence).first()
    assert intel and intel.generated_at is not None
    assert db.query(ProviderMaster).count() >= 6
    assert db.query(ProviderFieldMapping).count() >= 1
    db.close()
    assert len(TRIGGERS) == 4
    print("✓ Section 12 Trigger behaviors (upload history, intelligence timestamp, recommendation)")
    passed += 1

    sql_path = os.path.join(BACKEND_ROOT, "db", "postgresql", "16_physical_schema.sql")
    doc_path = os.path.join(PROJECT_ROOT, "docs", "16_Database_ERD_Physical_Schema.md")
    assert os.path.isfile(sql_path)
    assert os.path.isfile(doc_path)
    print("✓ Section 15 PostgreSQL schema SQL + documentation")
    passed += 1

    print(f"\nVolume 16 Physical Schema: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
