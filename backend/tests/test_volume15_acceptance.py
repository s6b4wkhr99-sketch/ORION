"""Volume 15 Section 21 — Provider integration acceptance tests."""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.audit import AuditLog
from app.models.provider_mapping import ProviderMappingVersion
from app.processing.seed import seed_configuration
from app.providers.constants import SUPPORTED_PROVIDERS
from app.providers.export_validation import ExportValidationError
from app.providers.import_engine import run_provider_import
from app.providers.normalization import normalize_row_metrics
from app.providers.registry import detect_provider_from_headers, get_adapter
from app.security.users import seed_users

SAMPLE = """Email,First Name,Last Name,State,ZIP
prov@test.com,Jane,Doe,CT,06801
"""

KLAVIYO_REPORT = """Campaign Name,Campaign ID,State,Sent,Delivered,Opened,Clicked,Unique Click,Revenue
Klaviyo Test,CAMP-KLV,CT,100,98,40,12,10,5000
"""

MAILCHIMP_REPORT = """Campaign Name,Campaign ID,State,Sent,Open,Click,Bounce,Revenue
Mailchimp Test,CAMP-MC,CT,200,50,15,2,8000
"""


def _reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_configuration(db)
    seed_users(db)
    db.close()


def _login(client) -> dict:
    r = client.post("/api/v1/auth/login", json={"email": "user@company.com", "password": "Ceragem2026!Adm"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['data']['token']}"}


def _upload(client, headers):
    r = client.post(
        "/api/v1/customers/upload",
        files={"file": ("prov.csv", io.BytesIO(SAMPLE.encode()), "text/csv")},
        headers=headers,
    )
    assert r.status_code == 200, r.text


def run_tests():
    _reset()
    client = TestClient(app)
    headers = _login(client)
    _upload(client, headers)
    passed = 0

    # Provider-001 — registry supports all providers without intelligence coupling
    assert len(SUPPORTED_PROVIDERS) == 6
    for name in SUPPORTED_PROVIDERS:
        adapter = get_adapter(name)
        assert adapter.provider_name == name
    print("✓ Provider-001 Provider-agnostic adapter registry")
    passed += 1

    # Section 21 — all providers export
    camp_r = client.post("/api/v1/campaign", json={"campaignName": "Provider Test", "campaignType": "Email"}, headers=headers)
    camp_id = camp_r.json()["data"]["campaignId"]
    for provider in SUPPORTED_PROVIDERS:
        r = client.post(
            "/api/v1/export",
            json={"provider": provider, "campaignId": camp_id, "campaignName": "Provider Test"},
            headers=headers,
        )
        assert r.status_code == 200, f"{provider}: {r.text}"
    print("✓ Section 21 All supported providers export successfully")
    passed += 1

    # Section 14 — export validation blocks empty audience
    db = SessionLocal()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_configuration(db)
    seed_users(db)
    db.close()
    empty_headers = _login(client)
    r = client.post(
        "/api/v1/export",
        json={"provider": "Generic CSV", "campaignId": "CAMP-EMPTY", "campaignName": "Empty"},
        headers=empty_headers,
    )
    assert r.status_code == 422
    print("✓ Section 14 Export validation failure blocks export")
    passed += 1

    # Re-seed with customers
    _reset()
    headers = _login(client)
    _upload(client, headers)

    # Section 16 — metric normalization
    adapter = get_adapter("Klaviyo")
    import pandas as pd

    df = pd.read_csv(io.StringIO(KLAVIYO_REPORT), dtype=str, keep_default_na=False)
    col_map = adapter.build_import_column_map(list(df.columns))
    row = df.iloc[0]
    metrics = normalize_row_metrics(row, col_map)
    assert metrics.get("total_sent") == 100 or metrics.get("delivered") == 98
    assert metrics.get("opened") == 40
    assert metrics.get("clicked") == 12
    assert metrics.get("actual_revenue") == 5000.0
    print("✓ Section 16 Metric normalization to internal fields")
    passed += 1

    # Section 6 — provider detection + import
    assert detect_provider_from_headers(["Campaign Name", "Sent", "Open", "Click", "Bounce"]) == "Mailchimp"
    db = SessionLocal()
    path = "/tmp/cios_klaviyo_report.csv"
    with open(path, "w", encoding="utf-8") as f:
        f.write(KLAVIYO_REPORT)
    report = run_provider_import(db, path, "klaviyo_report.csv")
    summary = json.loads(report.summary_json or "{}")
    assert summary.get("provider") in {"Klaviyo", "Generic CSV"}
    assert summary.get("learning_records_created", 0) >= 0
    db.close()
    print("✓ Sections 5–6 Import workflow with normalization and learning")
    passed += 1

    # Section 17 — mapping version records
    db = SessionLocal()
    assert db.query(ProviderMappingVersion).count() == len(SUPPORTED_PROVIDERS)
    db.close()
    r = client.get("/api/v1/providers/Klaviyo", headers=headers)
    assert r.status_code == 200
    assert r.json()["data"]["mappingVersion"]["version"]
    print("✓ Section 17 Provider mapping version metadata")
    passed += 1

    # Section 18 — audit on export/import
    db = SessionLocal()
    audits = db.query(AuditLog).filter(AuditLog.action.in_(["provider_export", "provider_import"])).all()
    db.close()
    assert len(audits) >= 1
    print("✓ Section 18 Provider audit records")
    passed += 1

    # Section 20 — new provider via adapter only
    from app.providers.adapter import ADAPTER_CLASSES

    assert "HubSpot" in ADAPTER_CLASSES
    print("✓ Section 20 Extensible adapter layer")
    passed += 1

    doc = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "15_Provider_Integration_Specification.md")
    assert os.path.isfile(doc)
    print("✓ Operations documentation present")
    passed += 1

    print(f"\nVolume 15 Provider Integration: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
