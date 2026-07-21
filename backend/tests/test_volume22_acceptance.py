"""Volume 22 — Reference Data Library acceptance tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.ai_engine.constants import PRODUCTS
from app.database import Base, SessionLocal, engine
from app.intelligence.purchase_power_rules import PURCHASE_POWER_LEVELS
from app.intelligence.prizm_rules import PRIZM_SEGMENTS
from app.main import app
from app.models.reference_data import ProductMaster, ReferenceDataVersion, StateMaster, ZipMaster
from app.models import *  # noqa: F401, F403
from app.processing.seed import seed_configuration
from app.providers.constants import SUPPORTED_PROVIDERS
from app.reference.registry import RDL_ACCEPTANCE_CRITERIA, RDL_VERSION, REFERENCE_DOMAINS, SUPPORTED_PRODUCTS
from app.reference.service import get_product_prices, get_products, get_reference_catalog
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

    assert len(REFERENCE_DOMAINS) == 8
    assert len(RDL_ACCEPTANCE_CRITERIA) == 9
    print("✓ Section 3 Reference Data architecture domains")
    passed += 1

    db = SessionLocal()
    try:
        assert db.query(ReferenceDataVersion).count() == 1
        assert db.query(StateMaster).count() >= 50
        assert db.query(ZipMaster).count() >= 10
        assert db.query(ProductMaster).count() == 7
        products = get_products(db)
        assert products[0]["productCode"] == "Master V9"
        prices = get_product_prices(db)
        assert prices["Master V9"] == 9999.0
        catalog = get_reference_catalog(db)
        assert catalog["version"]["libraryVersion"] == RDL_VERSION
        print("✓ Sections 4–18 Master tables seeded and version controlled")
        passed += 1
    finally:
        db.close()

    assert PRODUCTS == SUPPORTED_PRODUCTS
    assert PURCHASE_POWER_LEVELS == ("High", "Medium", "Low")
    assert len(PRIZM_SEGMENTS) == 9
    assert len(SUPPORTED_PROVIDERS) == 6
    print("✓ Section 21 Modules consume centralized reference data")
    passed += 1

    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"email": "user@company.com", "password": "Ceragem2026!Adm"})
    headers = {"Authorization": f"Bearer {login.json()['data']['token']}"}

    overview = _ok(client.get("/api/v1/reference", headers=headers))
    assert overview["counts"]["products"] == 7
    assert overview["counts"]["states"] >= 50
    print("✓ Reference catalog API")
    passed += 1

    products_api = _ok(client.get("/api/v1/reference/products", headers=headers))
    assert any(p["productCode"] == "Pause M6" for p in products_api["products"])
    print("✓ Product reference API (metadata-driven)")
    passed += 1

    segments = _ok(client.get("/api/v1/reference/segments", headers=headers))
    assert "Premium Wellness" in segments["ceragemSegments"]
    assert len(segments["prizmSegments"]) == 9
    print("✓ Intelligence reference API standardized")
    passed += 1

    geographic = _ok(client.get("/api/v1/reference/geographic", headers=headers))
    assert geographic["zipCount"] >= 10
    print("✓ Geographic enrichment centralized")
    passed += 1

    dashboards = _ok(client.get("/api/v1/reference/dashboards", headers=headers))
    assert len(dashboards["dashboards"]) >= 8
    assert len(dashboards["metrics"]) >= 7
    print("✓ Dashboard configuration metadata driven")
    passed += 1

    version = _ok(client.get("/api/v1/settings/reference", headers=headers))
    assert version["libraryVersion"] == RDL_VERSION
    print("✓ Settings reference version from RDL")
    passed += 1

    doc = os.path.join(PROJECT_ROOT, "docs", "22_Reference_Data_Library.md")
    assert os.path.isfile(doc)
    print("✓ Documentation complete")
    passed += 1

    print(f"\nVolume 22 Reference Data Library: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
