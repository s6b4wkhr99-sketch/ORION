"""Volume 18 Section 26 — AI Intelligence & Recommendation Engine acceptance tests."""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.ai_engine.constants import ENGINE_VERSION, MESSAGE_TYPES, PRODUCTS
from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.customer import Customer
from app.models.v16_schema import Recommendation
from app.processing.seed import seed_configuration
from app.rules.library import AI_RULE_MAP
from app.schema.apply import apply_physical_schema
from app.schema.seed_v16 import seed_v16_reference_schema
from app.security.users import seed_users

SAMPLE = "Email,First Name,Last Name,State,ZIP\nv18@test.com,V18,User,CT,06801\n"
CAMPAIGN = """Campaign Name,Campaign ID,State,Sent,Open,Click,Unique Click,Open Rate,CTR,Cost,Revenue,Category,Product,Click Count
V18 Test,CAMP-V18,CT,500,120,40,35,0.24,0.08,300,6000,Product,Master V9,40
"""

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
    client = TestClient(app)
    passed = 0

    login = client.post("/api/v1/auth/login", json={"email": "user@company.com", "password": "Ceragem2026!Adm"})
    headers = {"Authorization": f"Bearer {login.json()['data']['token']}"}

    upload = _ok(
        client.post(
            "/api/v1/customers/upload",
            files={"file": ("v18.csv", io.BytesIO(SAMPLE.encode()), "text/csv")},
            headers=headers,
        )
    )
    client.post(
        "/api/v1/report/upload",
        files={"file": ("v18-report.csv", io.BytesIO(CAMPAIGN.encode()), "text/csv")},
        headers=headers,
    )

    db = SessionLocal()
    customer = db.query(Customer).filter(Customer.email == "v18@test.com").first()
    assert customer is not None
    cid = str(customer.customer_id)
    rec_count = db.query(Recommendation).filter(Recommendation.customer_id == customer.customer_id).count()
    assert rec_count >= 1
    rec_row = db.query(Recommendation).filter(Recommendation.customer_id == customer.customer_id).first()
    assert rec_row.reason
    assert rec_row.engine_version
    assert rec_row.audit_json
    audit = json.loads(rec_row.audit_json)
    db.close()
    print("✓ Section 18 Recommendation database — every customer receives auditable recommendation")
    passed += 1

    full = _ok(client.get(f"/api/v1/intelligence/recommendation/{cid}", headers=headers))
    assert full["engine_version"] == ENGINE_VERSION
    assert full["product"]["primary"]
    assert full["product"]["confidence"] is not None
    assert full["product"]["confidence_category"]
    assert full["explanation"]["summary"]
    assert full["explanation"]["business_rules_used"]
    assert len(full["product"]["ranking"]) >= 3
    print("✓ Sections 13–15 Explainable ranked recommendation with confidence")
    passed += 1

    product = _ok(client.get(f"/api/v1/intelligence/recommendation/{cid}/product", headers=headers))
    assert product["primary"] in PRODUCTS or product["primary"] in {"Master S4", "MediSpa / Cellunic"}
    assert product["explanation"]
    print("✓ Section 6 Product recommendation engine API")
    passed += 1

    message = _ok(client.get(f"/api/v1/intelligence/recommendation/{cid}/message", headers=headers))
    assert message["primary"] in MESSAGE_TYPES
    print("✓ Section 7 Message recommendation engine API")
    passed += 1

    campaign = _ok(client.get(f"/api/v1/intelligence/recommendation/{cid}/campaign", headers=headers))
    assert campaign["recommended_campaign"]
    print("✓ Section 8 Campaign recommendation engine API")
    passed += 1

    geo = _ok(client.get(f"/api/v1/intelligence/recommendation/{cid}/geographic", headers=headers))
    assert geo["recommended_state"] == "CT"
    assert geo["recommended_zip"]
    print("✓ Section 9 Geographic recommendation engine API")
    passed += 1

    revenue = _ok(client.get(f"/api/v1/intelligence/prediction/revenue/{cid}", headers=headers))
    assert revenue["expected_revenue"] is not None
    assert "revenue_range" in revenue
    print("✓ Section 10 Revenue prediction engine API")
    passed += 1

    conversion = _ok(client.get(f"/api/v1/intelligence/prediction/conversion/{cid}", headers=headers))
    assert conversion["expected_conversion"] is not None
    assert conversion["campaign_priority"]
    print("✓ Section 11 Conversion prediction engine API")
    passed += 1

    assert full["scores"]["customer_score"] is not None
    assert full["business_priority"] in {"A", "B", "C", "D"}
    assert full["campaign_readiness"] in {"Ready", "Review", "Hold"}
    assert audit["engine_version"] == ENGINE_VERSION
    assert audit["reason"]
    print("✓ Sections 19–22 AI scoring, priority, readiness, audit")
    passed += 1

    assert len(AI_RULE_MAP) >= 6
    doc = os.path.join(PROJECT_ROOT, "docs", "18_AI_Intelligence_Recommendation_Engine.md")
    assert os.path.isfile(doc)
    print("✓ Section 26 Acceptance criteria + documentation")
    passed += 1

    print(f"\nVolume 18 AI Recommendation Engine: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
