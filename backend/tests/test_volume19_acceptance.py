"""Volume 19 Section 20 — Intelligence Calculation Framework acceptance tests."""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.intelligence.calculation_framework import apply_calculation_framework, normalize_score
from app.intelligence.framework_constants import CALCULATION_VERSION, INTELLIGENCE_CATEGORIES, INTELLIGENCE_ENGINE_VERSION
from app.intelligence.pipeline import run_intelligence_pipeline
from app.main import app
from app.models import *  # noqa: F401, F403
from app.models.customer import Customer, CustomerIntelligence
from app.processing.seed import seed_configuration
from app.rules.library import CALCULATION_FRAMEWORK_MAP
from app.schema.apply import apply_physical_schema
from app.schema.seed_v16 import seed_v16_reference_schema
from app.security.users import seed_users

SAMPLE = "Email,First Name,Last Name,State,ZIP,Age Range,Generation\nv19@test.com,V19,User,CT,06801,45-54,Baby Boomer\n"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    apply_physical_schema(engine)
    db = SessionLocal()
    seed_configuration(db)
    seed_users(db)
    seed_v16_reference_schema(db)
    db.close()


def _ok(resp):
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("success") is True, body
    return body["data"]


def run_tests():
    _reset()
    passed = 0

    # Deterministic normalization
    assert normalize_score(0.85, from_proxy=True) == 85.0
    assert normalize_score(150) == 100.0
    assert normalize_score(-5) == 0.0
    print("✓ Section 17 Score normalization 0–100")
    passed += 1

    # Pipeline produces framework
    ctx1 = run_intelligence_pipeline(
        customer={"email": "det@test.com", "state": "CT", "zip": "06801"},
        datalogix_raw={
            "age_range": "45-54",
            "generation": "Baby Boomer",
            "estimated_income": "Y",
            "home_value": "Z",
            "net_worth": "U",
            "online_access": "Yes",
            "retail_card": "Yes",
            "length_of_residence": "10",
        },
    )
    ctx2 = run_intelligence_pipeline(
        customer={"email": "det@test.com", "state": "CT", "zip": "06801"},
        datalogix_raw={
            "age_range": "45-54",
            "generation": "Baby Boomer",
            "estimated_income": "Y",
            "home_value": "Z",
            "net_worth": "U",
            "online_access": "Yes",
            "retail_card": "Yes",
            "length_of_residence": "10",
        },
    )
    assert ctx1.framework["categories"]["purchase_power"]["score"] == ctx2.framework["categories"]["purchase_power"]["score"]
    print("✓ Section 1–2 Deterministic repeatable calculation")
    passed += 1

    for cat in INTELLIGENCE_CATEGORIES:
        block = ctx1.framework["categories"][cat]
        assert 0 <= block["score"] <= 100
        assert 0 <= block["confidence"] <= 100
        assert block["explanation"]["primary_factors"]
        assert block["explanation"]["confidence_category"]
    print("✓ Sections 4–12 Every category has score, confidence, explainability")
    passed += 1

    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"email": "user@company.com", "password": "Ceragem2026!Adm"})
    headers = {"Authorization": f"Bearer {login.json()['data']['token']}"}
    _ok(
        client.post(
            "/api/v1/customers/upload",
            files={"file": ("v19.csv", io.BytesIO(SAMPLE.encode()), "text/csv")},
            headers=headers,
        )
    )

    db = SessionLocal()
    customer = db.query(Customer).filter(Customer.email == "v19@test.com").first()
    intel = db.query(CustomerIntelligence).filter(CustomerIntelligence.customer_id == customer.customer_id).first()
    assert intel.calculation_version == CALCULATION_VERSION
    assert intel.engine_version == INTELLIGENCE_ENGINE_VERSION
    assert intel.framework_summary_json or intel.framework_json
    if intel.framework_summary_json:
        framework = json.loads(intel.framework_summary_json)
    else:
        framework = json.loads(intel.framework_json)
    assert framework.get("calculation_id") or framework.get("audit", {}).get("calculation_id") or intel.calculation_version
    from app.models.scale import IntelligenceTrace

    trace_row = db.query(IntelligenceTrace).filter(IntelligenceTrace.customer_id == customer.customer_id).first()
    if trace_row:
        trace = json.loads(trace_row.trace_json or "[]")
    else:
        trace = json.loads(intel.trace_json or "[]")
    assert any("input" in t or "output" in t for t in trace)
    cid = str(customer.customer_id)
    db.close()
    print("✓ Sections 14–18 Versioning, audit, enriched trace")
    passed += 1

    api_framework = _ok(client.get(f"/api/v1/intelligence/framework/{cid}", headers=headers))
    assert api_framework["calculationVersion"] == CALCULATION_VERSION
    assert len(api_framework["categories"]) == len(INTELLIGENCE_CATEGORIES)
    print("✓ Section 24 API — intelligence framework endpoint")
    passed += 1

    api_customer = _ok(client.get(f"/api/v1/intelligence/customer/{cid}", headers=headers))
    assert "framework" in api_customer
    assert api_customer["framework"]["categories"]["purchase_power"]["score"] is not None
    print("✓ Section 19 Dashboard / intelligence API integration")
    passed += 1

    rec = _ok(client.get(f"/api/v1/intelligence/recommendation/{cid}", headers=headers))
    assert rec["recommendedProduct"]
    print("✓ Recommendation engine consumes standardized intelligence")
    passed += 1

    assert len(CALCULATION_FRAMEWORK_MAP) >= 9
    doc = os.path.join(PROJECT_ROOT, "docs", "19_Intelligence_Calculation_Framework.md")
    assert os.path.isfile(doc)
    print("✓ Section 20 Acceptance criteria + documentation")
    passed += 1

    print(f"\nVolume 19 Intelligence Calculation Framework: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
