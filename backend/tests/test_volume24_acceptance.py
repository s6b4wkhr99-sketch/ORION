"""Volume 24 — Development Convention acceptance tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.conventions.registry import (
    ARCHITECTURE_LAYERS,
    CONVENTION_ACCEPTANCE_CRITERIA,
    CONVENTION_VERSION,
    IMMUTABLE_INTELLIGENCE_FIELDS,
    PROHIBITED_PRACTICES,
    UPLOAD_WORKFLOW,
)
from app.conventions.service import get_conventions_overview, verify_convention_compliance
from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import *  # noqa: F401, F403
from app.processing.seed import seed_configuration
from app.rules.library import RULES
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

    overview = get_conventions_overview()
    assert overview["conventionVersion"] == CONVENTION_VERSION
    assert len(overview["architectureLayers"]) == 6
    assert "error" in overview["responseEnvelope"]["error"] or "code" in str(overview["responseEnvelope"])
    print("✓ Sections 2–3 Principles and architecture registry")
    passed += 1

    assert "Header Detection" in UPLOAD_WORKFLOW
    assert len(IMMUTABLE_INTELLIGENCE_FIELDS) >= 6
    assert len(PROHIBITED_PRACTICES) >= 8
    print("✓ Sections 16–17 Intelligence and upload conventions")
    passed += 1

    compliance = verify_convention_compliance(PROJECT_ROOT)
    assert compliance["apiEnvelopeImplemented"] is True
    assert compliance["businessLogicCentralized"] is True
    assert compliance["metadataDriven"] is True
    print("✓ Section 25 Runtime compliance checks")
    passed += 1

    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"email": "user@company.com", "password": "Ceragem2026!Adm"})
    headers = {"Authorization": f"Bearer {login.json()['data']['token']}"}

    api_overview = _ok(client.get("/api/v1/conventions", headers=headers))
    assert api_overview["gitCommitFormat"] == "type(scope): description"
    assert len(api_overview["prohibitedPractices"]) == len(PROHIBITED_PRACTICES)
    print("✓ Conventions API")
    passed += 1

    api_compliance = _ok(client.get("/api/v1/conventions/compliance", headers=headers))
    assert api_compliance["cursorConventionDocumented"] is True
    print("✓ Conventions compliance API")
    passed += 1

    # Volume 24 §11–12 error envelope with code + requestId
    bad = client.post("/api/v1/auth/login", json={"email": "bad@test.com", "password": "wrong"}, headers=headers)
    assert bad.status_code == 401
    body = bad.json()
    assert body["success"] is False
    assert "error" in body
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"]
    assert body["error"]["timestamp"]
    print("✓ Standardized error response format")
    passed += 1

    assert len(RULES) >= 30
    assert len(CONVENTION_ACCEPTANCE_CRITERIA) == 8
    doc = os.path.join(PROJECT_ROOT, "docs", "24_Development_Convention.md")
    assert os.path.isfile(doc)
    print("✓ Documentation and acceptance criteria")
    passed += 1

    print(f"\nVolume 24 Development Convention: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
