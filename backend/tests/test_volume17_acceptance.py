"""Volume 17 Section 26 — Analytics & Executive Intelligence acceptance tests."""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.analytics.kpi import EXECUTIVE_KPI_KEYS
from app.analytics.reports import REPORT_TYPES
from app.database import Base, SessionLocal, engine
from app.main import app
from app.processing.seed import seed_configuration
from app.schema.apply import apply_physical_schema
from app.schema.seed_v16 import seed_v16_reference_schema
from app.security.users import seed_users

SAMPLE = "Email,First Name,Last Name,State,ZIP\nv17@test.com,V17,User,CT,06801\n"
CAMPAIGN = """Campaign Name,Campaign ID,State,Sent,Open,Click,Unique Click,Open Rate,CTR,Cost,Revenue,Category,Product,Click Count
V17 Test,CAMP-V17,CT,500,120,40,35,0.24,0.08,300,6000,Product,Master V9,40
"""

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_ROOT)


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
    token = login.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/api/v1/customers/upload",
        files={"file": ("v17.csv", io.BytesIO(SAMPLE.encode()), "text/csv")},
        headers=headers,
    )
    client.post(
        "/api/v1/report/upload",
        files={"file": ("v17-report.csv", io.BytesIO(CAMPAIGN.encode()), "text/csv")},
        headers=headers,
    )

    executive = _ok(client.get("/api/v1/analytics/executive", headers=headers))
    assert "executive_kpi" in executive
    assert "customer_intelligence" in executive
    assert "campaign_intelligence" in executive
    assert "revenue_intelligence" in executive
    assert "geographic_intelligence" in executive
    assert "product_intelligence" in executive
    assert "forecast_intelligence" in executive
    assert "drill_down" in executive
    kpi_keys = {k["key"] for k in executive["executive_kpi"]}
    assert "total_customers" in kpi_keys
    assert "forecast_accuracy" in kpi_keys or executive["forecast_intelligence"].get("forecast_accuracy") is not None
    print("✓ Section 3–11 Executive dashboard with six intelligence areas")
    passed += 1

    revenue = executive["revenue_intelligence"]
    assert "expected_revenue" in revenue
    assert "actual_revenue" in revenue
    assert "revenue_gap" in revenue
    print("✓ Section 7 Revenue intelligence")
    passed += 1

    geo = executive["geographic_intelligence"]
    assert "revenue_by_state" in geo
    assert "revenue_by_zip" in geo
    assert "top_revenue_states" in geo
    print("✓ Section 8 Geographic intelligence (State + ZIP)")
    passed += 1

    learning = _ok(client.get("/api/v1/analytics/learning", headers=headers))
    assert "learning_score" in learning
    assert "forecast_accuracy" in learning
    print("✓ Section 12 Learning intelligence")
    passed += 1

    insights = _ok(client.get("/api/v1/analytics/insights", headers=headers))
    assert len(insights["insights"]) >= 3
    titles = {i["title"] for i in insights["insights"]}
    assert "Highest Performing State" in titles or "Best Performing Product" in titles
    print("✓ Section 14 Business insight engine")
    passed += 1

    recs = _ok(client.get("/api/v1/analytics/recommendations", headers=headers))
    assert len(recs["recommendations"]) >= 5
    categories = {r["category"] for r in recs["recommendations"]}
    assert "product" in categories
    assert "state" in categories or "campaign_type" in categories
    print("✓ Section 15 Executive recommendation engine")
    passed += 1

    compare = _ok(client.get("/api/v1/analytics/compare?type=state&a=CT&b=NY", headers=headers))
    assert compare["comparison_type"] == "state"
    assert "entity_a" in compare and "entity_b" in compare
    print("✓ Section 16 Comparative analysis")
    passed += 1

    trends = _ok(client.get("/api/v1/analytics/trends?metric=revenue&period=month", headers=headers))
    assert "series" in trends
    print("✓ Section 17 Trend analysis")
    passed += 1

    report = _ok(
        client.post(
            "/api/v1/analytics/reports/generate",
            json={"report_type": "daily_executive", "frequency": "daily", "format": "csv"},
            headers=headers,
        )
    )
    assert report["status"] == "completed"
    detail = _ok(client.get(f"/api/v1/analytics/reports/{report['reportId']}", headers=headers))
    assert detail["reportType"] == "daily_executive"
    print("✓ Section 18–19 Executive reports")
    passed += 1

    scorecard = _ok(client.get("/api/v1/analytics/scorecard", headers=headers))
    assert "overall_business_score" in scorecard
    assert len(scorecard["dimensions"]) >= 7
    print("✓ Section 25 Executive scorecard")
    passed += 1

    alerts = _ok(client.get("/api/v1/analytics/alerts", headers=headers))
    assert "alerts" in alerts
    print("✓ Section 24 Executive alerts")
    passed += 1

    export_resp = client.get("/api/v1/analytics/export", headers=headers)
    assert export_resp.status_code == 200
    assert "total_customers" in export_resp.text or "expected_revenue" in export_resp.text
    print("✓ Section 23 Analytics export (CSV KPIs)")
    passed += 1

    assert len(EXECUTIVE_KPI_KEYS) >= 12
    assert len(REPORT_TYPES) >= 5
    doc_path = os.path.join(PROJECT_ROOT, "docs", "17_Analytics_Executive_Intelligence.md")
    assert os.path.isfile(doc_path)
    print("✓ Section 20–26 KPI library, documentation, acceptance criteria")
    passed += 1

    print(f"\nVolume 17 Analytics & Executive Intelligence: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
