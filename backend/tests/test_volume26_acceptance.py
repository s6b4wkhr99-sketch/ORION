"""Volume 26 — CIOS Design Principles acceptance tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.design_principles.registry import (
    CONSTITUTION,
    DESIGN_PRINCIPLES_ACCEPTANCE_CRITERIA,
    DESIGN_PRINCIPLES_VERSION,
    FINAL_STATEMENT,
    PRINCIPLES,
    VISION,
)
from app.design_principles.service import get_design_principles_overview, verify_design_principles_compliance
from app.main import app
from app.models import *  # noqa: F401, F403
from app.processing.seed import seed_configuration
from app.schema.apply import apply_physical_schema
from app.schema.seed_v16 import seed_v16_reference_schema
from app.security.users import seed_users

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

    overview = get_design_principles_overview()
    assert overview["designPrinciplesVersion"] == DESIGN_PRINCIPLES_VERSION
    assert overview["vision"] == VISION
    assert len(overview["principles"]) == len(PRINCIPLES) == 23
    assert overview["principles"][0]["id"] == "01"
    assert overview["principles"][-1]["id"] == "23"
    assert overview["finalStatement"] == FINAL_STATEMENT
    print("✓ Sections 2–25 Vision, principles and final statement registry")
    passed += 1

    assert len(CONSTITUTION) == 4
    assert CONSTITUTION[-1]["resolution"] == "protect Customer Intelligence"
    assert len(DESIGN_PRINCIPLES_ACCEPTANCE_CRITERIA) == 7
    print("✓ CIOS Constitution and acceptance criteria")
    passed += 1

    compliance = verify_design_principles_compliance(PROJECT_ROOT)
    assert compliance["allPrinciplesDocumented"] is True
    assert compliance["constitutionDocumented"] is True
    assert compliance["businessRulesBeforeAi"] is True
    assert compliance["metadataDriven"] is True
    assert compliance["automationByDefault"] is True
    assert compliance["securityBuiltIn"] is True
    assert compliance["actionsAuditable"] is True
    assert compliance["volume26Documented"] is True
    print("✓ Runtime architectural alignment compliance checks")
    passed += 1

    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"email": "user@company.com", "password": "Ceragem2026!Adm"})
    headers = {"Authorization": f"Bearer {login.json()['data']['token']}"}

    api_overview = _ok(client.get("/api/v1/design-principles", headers=headers))
    assert len(api_overview["principles"]) == 23
    assert len(api_overview["explainabilityFields"]) == 5
    assert api_overview["principles"][2]["title"] == "Recommendation Must Be Explainable"
    print("✓ Design principles API")
    passed += 1

    api_compliance = _ok(client.get("/api/v1/design-principles/compliance", headers=headers))
    assert api_compliance["principleCount"] == 23
    assert api_compliance["principlesRegistryPresent"] is True
    print("✓ Design principles compliance API")
    passed += 1

    doc = os.path.join(PROJECT_ROOT, "docs", "26_CIOS_Design_Principles.md")
    assert os.path.isfile(doc)
    print("✓ Documentation artifact")
    passed += 1

    print(f"\nVolume 26 CIOS Design Principles: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
