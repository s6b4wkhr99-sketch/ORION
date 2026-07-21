"""Volume 20 Section 24 — Le Frame methodology acceptance tests."""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.intelligence.datalogix_engine import preserve_datalogix_value
from app.main import app
from app.methodology.registry import (
    CERAGEM_SEGMENTS,
    CONVERSION_STAGES,
    EXPLAINABILITY_REQUIREMENTS,
    GOVERNANCE_REQUIREMENTS,
    INTELLIGENCE_LAYERS,
    INTELLIGENCE_PYRAMID,
    METHODOLOGY_VERSION,
    SUCCESS_CRITERIA,
)
from app.methodology.service import get_methodology_overview
from app.processing.seed import seed_configuration
from app.schema.apply import apply_physical_schema
from app.schema.seed_v16 import seed_v16_reference_schema
from app.security.users import seed_users

SAMPLE = "Email,First Name,Last Name,State,ZIP,Age Range,Generation\nv20@test.com,V20,User,CT,06801,45-54,Baby Boomer\n"
CAMPAIGN = """Campaign Name,Campaign ID,State,Sent,Open,Click,Unique Click,Open Rate,CTR,Cost,Revenue,Category,Product,Click Count
V20 Test,CAMP-V20,CT,500,120,40,35,0.24,0.08,300,6000,Product,Master V9,40
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
    passed = 0

    assert len(INTELLIGENCE_PYRAMID) >= 7
    assert len(INTELLIGENCE_LAYERS) == 7
    assert len(CERAGEM_SEGMENTS) == 8
    assert len(CONVERSION_STAGES) == 9
    print("✓ Sections 3–4 Pyramid and seven intelligence layers")
    passed += 1

    assert preserve_datalogix_value("estimated_income", "Y") == "Y"
    assert preserve_datalogix_value("net_worth", "U") == "U"
    print("✓ Section 6 Datalogix categorical preservation")
    passed += 1

    db = SessionLocal()
    overview = get_methodology_overview(db)
    db.close()
    assert overview["methodologyVersion"] == METHODOLOGY_VERSION
    assert overview["philosophy"]
    assert overview["strategicDifferentiation"]["cios"]
    print("✓ Sections 2, 22 Strategic philosophy and differentiation")
    passed += 1

    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"email": "user@company.com", "password": "Ceragem2026!Adm"})
    headers = {"Authorization": f"Bearer {login.json()['data']['token']}"}

    _ok(
        client.post(
            "/api/v1/customers/upload",
            files={"file": ("v20.csv", io.BytesIO(SAMPLE.encode()), "text/csv")},
            headers=headers,
        )
    )
    client.post(
        "/api/v1/report/upload",
        files={"file": ("v20-report.csv", io.BytesIO(CAMPAIGN.encode()), "text/csv")},
        headers=headers,
    )

    methodology = _ok(client.get("/api/v1/methodology", headers=headers))
    assert methodology["layers"][0]["name"] == "Raw Customer Data"
    assert methodology["layers"][6]["name"] == "Continuous Learning"
    assert len(methodology["explainabilityRequirements"]) == len(EXPLAINABILITY_REQUIREMENTS)
    print("✓ Section 19 Explainable intelligence requirements exposed")
    passed += 1

    pyramid = _ok(client.get("/api/v1/methodology/pyramid", headers=headers))
    assert len(pyramid["pyramid"]) >= 7
    print("✓ Section 3 Pyramid API")
    passed += 1

    layers = _ok(client.get("/api/v1/methodology/layers", headers=headers))
    assert len(layers["layers"]) == 7
    print("✓ Section 4 Layers API")
    passed += 1

    governance = _ok(client.get("/api/v1/methodology/governance", headers=headers))
    assert len(governance["requirements"]) == len(GOVERNANCE_REQUIREMENTS)
    assert len(governance["successCriteria"]) == len(SUCCESS_CRITERIA)
    print("✓ Section 23 Methodology governance")
    passed += 1

    success = _ok(client.get("/api/v1/methodology/success-criteria", headers=headers))
    assert success["allMet"] is True
    assert len(success["criteria"]) == 8
    print("✓ Section 24 Success criteria verified at runtime")
    passed += 1

    doc = os.path.join(PROJECT_ROOT, "docs", "20_Le_Frame_Customer_Intelligence_Methodology.md")
    assert os.path.isfile(doc)
    print("✓ Documentation and acceptance criteria complete")
    passed += 1

    print(f"\nVolume 20 Le Frame Methodology: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
