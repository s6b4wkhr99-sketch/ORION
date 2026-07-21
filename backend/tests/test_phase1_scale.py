"""Phase 1 — Scale optimization acceptance tests (tiered trace, rollup, batch upload)."""

import io
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.acquisition.rollup import has_upload_rollup
from app.database import Base, SessionLocal, engine
from app.intelligence.trace_backfill import backfill_legacy_traces, count_legacy_inline_rows
from app.intelligence.trace_storage import build_framework_summary, build_trace_summary
from app.main import app
from app.models import *  # noqa: F401, F403
from app.models.customer import CustomerIntelligence
from app.models.scale import IntelligenceTrace, UploadRollup
from app.processing.seed import seed_configuration
from app.schema.apply import apply_physical_schema
from app.schema.seed_v16 import seed_v16_reference_schema
from app.security.users import seed_users
from tests.qa_helpers import ADMIN_EMAIL, ADMIN_PASSWORD


def _reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    apply_physical_schema(engine)
    db = SessionLocal()
    seed_configuration(db)
    seed_users(db)
    seed_v16_reference_schema(db)
    db.close()


def run_tests() -> int:
    _reset()
    client = TestClient(app)
    login_resp = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    headers = {"Authorization": f"Bearer {login_resp.json()['data']['token']}"}
    passed = 0

    trace = [
        {
            "rule_id": "Rule-001",
            "business_rule_id": "BR-001",
            "name": "Email Validation",
            "explanation": "Valid email detected",
            "input": {"email": "a@test.com"},
            "output": {"valid": True},
        }
    ]
    framework = {
        "calculation_id": "calc-1",
        "calculation_version": "v19",
        "engine_version": "v1",
        "categories": {"purchase_power": {"score": 0.8, "level": "High", "confidence": 0.9, "explanation": "Strong"}},
        "audit": {"rule_version": "v4", "timestamp": "2026-07-07T00:00:00Z"},
    }
    summary = build_trace_summary(trace, framework)
    fw_summary = build_framework_summary(framework)
    assert summary["rule_count"] == 1
    assert summary["business_rule_ids"] == ["BR-001"]
    assert "purchase_power" in fw_summary["categories"]
    assert len(json.dumps(summary)) < 2000
    print("✓ Trace and framework summary builders stay compact")
    passed += 1

    csv = (
        "Email,State,ZIP Code\n"
        "phase1a@test.com,NJ,07650\n"
        "phase1b@test.com,NJ,07651\n"
    )
    upload_resp = client.post(
        "/api/v1/customers/upload",
        files={"file": ("phase1.csv", io.BytesIO(csv.encode()), "text/csv")},
        headers=headers,
    )
    assert upload_resp.status_code == 200, upload_resp.text
    upload_data = upload_resp.json()["data"]
    upload_id = upload_data["uploadId"]
    upload_uuid = uuid.UUID(upload_id)

    db = SessionLocal()
    customer_id = None
    try:
        assert has_upload_rollup(db, upload_uuid)
        rollup_count = db.query(UploadRollup).filter(UploadRollup.upload_id == upload_uuid).count()
        assert rollup_count > 0

        intel = db.query(CustomerIntelligence).first()
        assert intel is not None
        customer_id = str(intel.customer_id)
        assert intel.trace_summary_json
        assert intel.framework_summary_json
        assert intel.trace_json is None
        assert intel.framework_json is None
        assert len(intel.trace_summary_json) < 5000

        trace_row = db.query(IntelligenceTrace).filter(IntelligenceTrace.customer_id == intel.customer_id).first()
        assert trace_row is not None
        full_trace = json.loads(trace_row.trace_json)
        assert len(full_trace) > 0

        state_dash = client.get(f"/api/v1/dashboard/state?upload_id={upload_id}", headers=headers)
        assert state_dash.status_code == 200
        dash = state_dash.json()["data"]
        assert dash.get("rollup_source") is True
        assert dash["kpis"]["target_customers"] >= 2
    finally:
        db.close()

    print("✓ Upload stores tiered trace, rollup, and rollup-backed state dashboard")
    passed += 1

    framework_resp = client.get(f"/api/v1/intelligence/framework/{customer_id}", headers=headers)
    assert framework_resp.status_code == 200, framework_resp.text
    fw = framework_resp.json()["data"]
    assert fw["ruleTrace"]
    assert fw["categories"]
    print("✓ Full explainability available via intelligence_trace on demand")
    passed += 1

    db = SessionLocal()
    try:
        legacy_intel = db.query(CustomerIntelligence).first()
        assert legacy_intel is not None
        legacy_intel.trace_json = json.dumps(
            [
                {
                    "rule_id": "Rule-legacy",
                    "business_rule_id": "BR-legacy",
                    "explanation": "Legacy inline trace",
                }
            ]
        )
        legacy_intel.framework_json = json.dumps(framework)
        legacy_intel.trace_summary_json = None
        legacy_intel.framework_summary_json = None
        db.query(IntelligenceTrace).filter(IntelligenceTrace.customer_id == legacy_intel.customer_id).delete()
        db.commit()
        assert count_legacy_inline_rows(db) >= 1

        stats = backfill_legacy_traces(db, batch_size=10, commit_every=10)
        assert stats["processed"] >= 1
        assert stats["inline_cleared"] >= 1
        assert count_legacy_inline_rows(db) == 0

        db.refresh(legacy_intel)
        assert legacy_intel.trace_json is None
        assert legacy_intel.framework_json is None
        assert legacy_intel.trace_summary_json
        assert legacy_intel.framework_summary_json

        trace_row = (
            db.query(IntelligenceTrace).filter(IntelligenceTrace.customer_id == legacy_intel.customer_id).first()
        )
        assert trace_row is not None
        migrated_trace = json.loads(trace_row.trace_json)
        assert migrated_trace[0]["rule_id"] == "Rule-legacy"
    finally:
        db.close()

    print("✓ Legacy inline trace backfill migrates to intelligence_trace")
    passed += 1

    print(f"\nPhase 1 Scale Optimization: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
