"""Volume 07 Section 16 — API acceptance tests."""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import *  # noqa: F401, F403 — register RFC-001 tables for create_all
from app.processing.seed import seed_configuration

SAMPLE_CUSTOMERS = """Email,First Name,Last Name,State,ZIP,Age Range,Generation,Gender,Estimated Income,Home Value,Household,Length of Residence,Net Worth,Online Access,Retail Card,Dwelling,Bank Card,Adults,Children,Persons
api@test.com,Api,User,CT,06801,45-54,Baby Boomer,M,150000,500000,2,10,750000,Yes,Yes,Single Family,Yes,2,0,2
"""

SAMPLE_CAMPAIGN = """Campaign Name,Campaign ID,State,Sent,Open,Click,Unique Click,Open Rate,CTR,Cost,Revenue,Category,Product,Click Count
API Test,CAMP-API01,CT,500,120,40,35,0.24,0.08,300,6000,Product,Master V9,40
"""


def _reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_configuration(db)
    db.close()


def _assert_success(resp):
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("success") is True, body
    return body["data"]


def run_tests():
    _reset()
    client = TestClient(app)
    passed = 0

    # Authentication
    r = client.post("/api/v1/auth/login", json={"email": "user@company.com", "password": "Ceragem2026!Adm"})
    data = _assert_success(r)
    token = data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Authentication succeeds")
    passed += 1

    # Customer Upload
    files = {"file": ("api_customers.csv", io.BytesIO(SAMPLE_CUSTOMERS.encode()), "text/csv")}
    r = client.post("/api/v1/customers/upload?sync=true", files=files, headers=headers)
    upload = _assert_success(r)
    assert upload["status"] == "completed"
    print("✓ Customer Upload succeeds")
    passed += 1

    # Intelligence generated (customer list)
    r = client.get("/api/v1/customers?limit=10", headers=headers)
    customers = _assert_success(r)
    assert customers["total"] >= 1
    cid = customers["rows"][0]["id"]
    r = client.get(f"/api/v1/intelligence/customer/{cid}", headers=headers)
    intel = _assert_success(r)
    assert intel["prizmProxy"] is not None or intel.get("ceragemSegment")
    print("✓ Intelligence generated")
    passed += 1

    # Campaign created
    r = client.post("/api/v1/campaign", json={"campaignName": "API Test Campaign", "campaignType": "Email"}, headers=headers)
    camp = _assert_success(r)
    camp_id = camp["campaignId"]
    print("✓ Campaign created")
    passed += 1

    # Forecast generated
    r = client.get(f"/api/v1/campaign/{camp_id}/forecast", headers=headers)
    forecast = _assert_success(r)
    assert forecast["forecast"]["expected_revenue"] >= 0
    print("✓ Forecast generated")
    passed += 1

    # Revenue Forecast API
    r = client.get("/api/v1/forecast/revenue?targetCustomers=1000", headers=headers)
    rev = _assert_success(r)
    assert rev["expected_revenue"] > 0
    print("✓ Revenue Forecast generated")
    passed += 1

    # Export generated
    r = client.post("/api/v1/export", json={"provider": "Generic CSV", "campaignId": camp_id, "campaignName": "API Test"}, headers=headers)
    export = _assert_success(r)
    assert export["downloadUrl"]
    print("✓ Export generated")
    passed += 1

    # Campaign Report imported
    files = {"file": ("api_report.csv", io.BytesIO(SAMPLE_CAMPAIGN.encode()), "text/csv")}
    r = client.post("/api/v1/report/upload", files=files, headers=headers)
    report = _assert_success(r)
    assert report["status"] == "completed"
    print("✓ Campaign Report imported")
    passed += 1

    # Dashboard updated
    r = client.get("/api/v1/dashboard/executive", headers=headers)
    exec_dash = _assert_success(r)
    assert exec_dash["total_customers"] >= 1
    print("✓ Dashboard updated")
    passed += 1

    # Recommendation generated
    r = client.get(f"/api/v1/intelligence/recommendation/{cid}", headers=headers)
    rec = _assert_success(r)
    assert "recommendedProduct" in rec
    print("✓ Recommendation generated")
    passed += 1

    print(f"\nAll {passed}/10 Volume 07 API acceptance criteria passed.")


if __name__ == "__main__":
    run_tests()
