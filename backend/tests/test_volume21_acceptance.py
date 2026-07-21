"""Volume 21 Section 18 — Master index and knowledge governance acceptance tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.knowledge.registry import (
    DATABASE_CROSS_REFERENCE,
    DOCUMENT_VOLUMES,
    GLOSSARY,
    KNOWLEDGE_VERSION,
    MASTER_ACCEPTANCE_CRITERIA,
    MASTER_NAVIGATION,
    PROVIDER_INDEX,
)
from app.knowledge.service import get_knowledge_overview
from app.main import app
from app.processing.seed import seed_configuration
from app.providers.adapter import ADAPTER_CLASSES
from app.rules.library import RULES
from app.schema.apply import apply_physical_schema
from app.schema.registry import TABLE_MAP
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

    assert len(DOCUMENT_VOLUMES) == 26
    assert len(MASTER_NAVIGATION) == 10
    assert len(GLOSSARY) == 8
    assert len(PROVIDER_INDEX) == 6
    print("✓ Sections 2–3 Documentation structure and master navigation")
    passed += 1

    spec_tables = {item["table"] for item in DATABASE_CROSS_REFERENCE}
    assert spec_tables.issubset(set(TABLE_MAP.keys()))
    assert len(RULES) >= 30
    print("✓ Sections 5–7 Database, intelligence and business rule cross references")
    passed += 1

    provider_names = {p["provider"] for p in PROVIDER_INDEX}
    assert provider_names == set(ADAPTER_CLASSES.keys())
    print("✓ Sections 12–13 Provider and data source index")
    passed += 1

    db = SessionLocal()
    overview = get_knowledge_overview(db)
    db.close()
    assert overview["knowledgeVersion"] == KNOWLEDGE_VERSION
    assert overview["ruleCount"] == len(RULES)
    assert overview["tableCount"] == len(TABLE_MAP)
    print("✓ Section 1 Documentation hub overview service")
    passed += 1

    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"email": "user@company.com", "password": "Ceragem2026!Adm"})
    headers = {"Authorization": f"Bearer {login.json()['data']['token']}"}

    knowledge = _ok(client.get("/api/v1/knowledge", headers=headers))
    assert len(knowledge["documentVolumes"]) == 26
    assert len(knowledge["workflowCrossReference"]) >= 7
    print("✓ Section 1 Knowledge API overview")
    passed += 1

    index = _ok(client.get("/api/v1/knowledge/index", headers=headers))
    assert index["documentVolumes"][0]["volume"] == "01"
    assert index["documentVolumes"][-1]["volume"] == "26"
    print("✓ Section 4 Documentation dependency map exposed")
    passed += 1

    xref = _ok(client.get("/api/v1/knowledge/cross-reference", headers=headers))
    assert len(xref["database"]) == len(DATABASE_CROSS_REFERENCE)
    assert len(xref["apis"]) >= 9
    print("✓ Sections 5–10 Cross-reference API")
    passed += 1

    governance = _ok(client.get("/api/v1/knowledge/governance", headers=headers))
    assert len(governance["versionGovernanceFields"]) == 8
    assert len(governance["masterAcceptanceCriteria"]) == len(MASTER_ACCEPTANCE_CRITERIA)
    print("✓ Sections 16–17 Version and documentation governance")
    passed += 1

    glossary = _ok(client.get("/api/v1/knowledge/glossary", headers=headers))
    assert glossary["glossary"][0]["term"] == "Customer Intelligence"
    print("✓ Section 15 Glossary API")
    passed += 1

    acceptance = _ok(client.get("/api/v1/knowledge/acceptance-criteria", headers=headers))
    assert acceptance["allMet"] is True
    assert len(acceptance["criteria"]) == 9
    print("✓ Section 18 Master acceptance criteria verified at runtime")
    passed += 1

    doc = os.path.join(PROJECT_ROOT, "docs", "21_Master_Index_Cross_Reference_Knowledge_Governance.md")
    assert os.path.isfile(doc)
    print("✓ Documentation and acceptance criteria complete")
    passed += 1

    print(f"\nVolume 21 Master Index: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
