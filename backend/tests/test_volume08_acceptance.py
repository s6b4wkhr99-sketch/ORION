"""Volume 08 Section 20 — Required acceptance tests."""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.intelligence.datalogix_engine import preserve_datalogix_value
from app.main import app
from app.processing.mapper import build_column_map, validate_column_map
from app.processing.seed import seed_configuration
from app.intelligence.pipeline import run_segmentation

SAMPLE = """Email,First Name,Last Name,State,ZIP,Age Range,Generation,Gender,Estimated Income,Home Value,Household,Length of Residence,Net Worth,Online Access,Retail Card,Dwelling,Bank Card,Adults,Children,Persons
v08@test.com,V08,User,CT,06801,45-54,Baby Boomer,M,X,Y,Z,10,750000,Yes,Yes,Single Family,Yes,2,0,2
"""

CAMPAIGN = """Campaign Name,Campaign ID,State,Sent,Open,Click,Unique Click,Open Rate,CTR,Cost,Revenue,Category,Product,Click Count
V08 Test,CAMP-V08,CT,500,120,40,35,0.24,0.08,300,6000,Product,Master V9,40
"""


def _reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_configuration(db)
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

    # Datalogix preservation
    assert preserve_datalogix_value("estimated_income", "X") == "X"
    assert preserve_datalogix_value("estimated_income", "Y") == "Y"
    assert preserve_datalogix_value("home_value", "Z") == "Z"
    assert preserve_datalogix_value("net_worth", "U") == "U"
    print("✓ Datalogix preservation test")
    passed += 1

    # Mapping test
    db = SessionLocal()
    try:
        headers = [h.strip() for h in SAMPLE.splitlines()[0].split(",")]
        col_map = build_column_map(db, headers)
        validation = validate_column_map(db, col_map)
        assert validation["is_valid"] is True
        assert "email_address" in validation["mapped_columns"]
    finally:
        db.close()
    print("✓ Mapping test")
    passed += 1

    # Intelligence generation (segmentation entry point)
    result = run_segmentation(
        {"state": "CT", "zip": "06801"},
        {
            "estimated_income_code": "150000",
            "home_value_code": "500000",
            "age_range": "45-54",
            "generation": "Baby Boomer",
            "gender": "M",
            "length_of_residence": "10",
            "net_worth_indicator": "750000",
            "online_access_code": "Yes",
            "retail_card_code": "Yes",
            "adults_in_household": "2",
            "children_in_household": "0",
        },
        None,
    )
    for field in (
        "prizm_proxy_segment",
        "ceragem_segment",
        "message_direction",
        "purchase_power",
        "pain_index",
        "lifestyle",
        "recommended_product",
        "expected_revenue",
        "campaign_priority",
    ):
        assert field in result, f"missing {field}"
    print("✓ Intelligence generation test")
    passed += 1

    # Upload test
    r = client.post("/api/v1/auth/login", json={"email": "user@company.com", "password": "Ceragem2026!Adm"})
    token = _ok(r)["token"]
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("v08_customers.csv", io.BytesIO(SAMPLE.encode()), "text/csv")}
    upload = _ok(client.post("/api/v1/customers/upload", files=files, headers=headers))
    assert upload["status"] == "completed"
    print("✓ Upload test")
    passed += 1

    # Dashboard data test
    summary = _ok(client.get("/api/v1/dashboard/executive", headers=headers))
    assert summary.get("total_customers", 0) >= 1
    print("✓ Dashboard data test")
    passed += 1

    # Campaign creation test
    camp = _ok(
        client.post(
            "/api/v1/campaign",
            json={"campaignName": "V08 Campaign", "campaignType": "Product Promotion"},
            headers=headers,
        )
    )
    campaign_id = camp["campaignId"]
    print("✓ Campaign creation test")
    passed += 1

    # Revenue forecast test
    forecast = _ok(client.get(f"/api/v1/campaign/{campaign_id}/forecast", headers=headers))
    assert "expectedRevenue" in forecast or "totalExpectedRevenue" in forecast or "forecast" in forecast
    print("✓ Revenue forecast test")
    passed += 1

    # Export test
    export = _ok(
        client.post(
            "/api/v1/export",
            json={"provider": "Generic CSV", "campaignId": campaign_id, "campaignName": "V08 Campaign"},
            headers=headers,
        )
    )
    assert export.get("exportId") or export.get("downloadUrl")
    print("✓ Export test")
    passed += 1

    # Campaign report import test
    files = {"file": ("v08_report.csv", io.BytesIO(CAMPAIGN.encode()), "text/csv")}
    report = _ok(client.post("/api/v1/report/upload", files=files, headers=headers))
    assert report.get("status") == "completed"
    print("✓ Campaign report import test")
    passed += 1

    # ROI / standardized error envelope
    roi = _ok(client.get("/api/v1/dashboard/roi", headers=headers))
    assert isinstance(roi, dict)
    print("✓ ROI dashboard test")
    passed += 1

    bad = client.get("/api/v1/customers/not-a-uuid", headers=headers)
    assert bad.status_code in (404, 422, 400)
    body = bad.json()
    assert body.get("success") is False
    assert "message" in body
    print("✓ Standardized error response test")
    passed += 1

    print(f"\nVolume 08 acceptance: {passed}/{passed} passed")
    return passed


if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as exc:
        print(f"\nFAILED: {exc}")
        raise SystemExit(1)
