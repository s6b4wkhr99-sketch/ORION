"""Volume 06 Section 26 — Campaign acceptance tests."""

import io
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.acquisition.upload import process_upload, save_upload_file
from app.campaign.detail import get_campaign_detail
from app.campaign.export import generate_export
from app.campaign.forecast import compute_campaign_forecast, forecast_accuracy
from app.campaign.reports import process_campaign_report
from app.database import Base, SessionLocal, engine
from app.models.campaign import Campaign
from app.models.learning import CampaignLearning
from app.processing.seed import seed_configuration

SAMPLE_CUSTOMERS = """Email,First Name,Last Name,State,ZIP,Age Range,Generation,Gender,Estimated Income,Home Value,Household,Length of Residence,Net Worth,Online Access,Retail Card,Dwelling,Bank Card,Adults,Children,Persons
john@test.com,John,Doe,CT,06801,45-54,Baby Boomer,M,150000,500000,2,10,750000,Yes,Yes,Single Family,Yes,2,0,2
jane@test.com,Jane,Smith,CT,06802,55-64,Baby Boomer,F,125000,450000,1,15,600000,Yes,No,Single Family,Yes,1,0,1
"""

SAMPLE_CAMPAIGN = """Campaign Name,Campaign ID,State,Sent,Open,Click,Unique Click,Open Rate,CTR,Cost,Revenue,Category,Product,Click Count
Spring Wellness,CAMP-TEST01,CT,1000,250,75,60,0.25,0.075,500,12000,Product,Master V9,75
"""


def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_configuration(db)
    db.close()


def test_001_campaign_creation():
    db = SessionLocal()
    campaign = Campaign(
        campaign_id="CAMP-ACCEPT-001",
        campaign_name="Acceptance Test Campaign",
        campaign_type="Email",
        status="draft",
        provider="mass_email",
        owner="CIOS Admin",
    )
    db.add(campaign)
    db.commit()
    found = db.query(Campaign).filter(Campaign.campaign_id == "CAMP-ACCEPT-001").first()
    db.close()
    assert found is not None
    print("TEST-001 PASS: Campaign created successfully.")


def test_002_audience_builder():
    db = SessionLocal()
    path = save_upload_file(SAMPLE_CUSTOMERS.encode(), "acceptance_customers.csv")
    upload = process_upload(db, path, "acceptance_customers.csv")
    db.close()
    assert upload.status == "completed"
    print("TEST-002 PASS: Customer Intelligence generates audience correctly.")


def test_003_forecast():
    result = compute_campaign_forecast(
        target_customers=1000,
        ceragem_distribution={"High + Wellness": 400, "Mid-Low + Pain Index": 600},
        product_distribution={"Master V9": 400, "Pause M6": 600},
        campaign_type="Email",
    )
    assert result["expected_revenue"] > 0
    assert result["expected_orders"] > 0
    print(f"TEST-003 PASS: Revenue Forecast generated — ${result['expected_revenue']:,.2f}")


def test_004_export():
    db = SessionLocal()
    _, job = generate_export(db, provider_name="Generic CSV", campaign_name="Acceptance Campaign", campaign_id="CAMP-ACCEPT-001")
    db.close()
    assert job.export_id is not None
    print("TEST-004 PASS: Provider-ready file generated.")


def test_005_campaign_report_import():
    db = SessionLocal()
    path = save_upload_file(SAMPLE_CAMPAIGN.encode(), "acceptance_campaign.csv")
    report = process_campaign_report(db, path, "acceptance_campaign.csv")
    db.close()
    assert report.status == "completed"
    print("TEST-005 PASS: Campaign metrics imported successfully.")


def test_006_dashboard_update():
    db = SessionLocal()
    from app.campaign.analytics import get_executive_summary
    summary = get_executive_summary(db)
    db.close()
    assert summary["total_customers"] >= 2
    print("TEST-006 PASS: Executive Dashboard reflects campaign results.")


def test_007_learning():
    db = SessionLocal()
    records = db.query(CampaignLearning).filter(CampaignLearning.campaign_id == "CAMP-TEST01").all()
    db.close()
    assert len(records) >= 1
    print(f"TEST-007 PASS: Learning record created (count={len(records)}).")


def test_008_revenue_calculation():
    expected = compute_campaign_forecast(target_customers=1000, ceragem_distribution={"High + Wellness": 1000})
    actual_revenue = 12000.0
    accuracy = forecast_accuracy(actual_revenue, expected["expected_revenue"])
    incentive = expected["le_frame_incentive"]
    assert expected["expected_revenue"] > 0
    assert incentive == round(expected["expected_revenue"] * 0.15, 4)
    print(f"TEST-008 PASS: Expected=${expected['expected_revenue']:,.2f} Actual=$12,000 Accuracy={accuracy} LeFrame=${incentive:,.2f}")


def test_campaign_detail_api():
    db = SessionLocal()
    detail = get_campaign_detail(db, "CAMP-TEST01")
    db.close()
    assert "header" in detail
    assert detail["kpis"]["sent"] > 0
    print("TEST-DETAIL PASS: Campaign detail dashboard data available.")


if __name__ == "__main__":
    print("Running Volume 06 Campaign Acceptance Tests...\n")
    _reset_db()
    test_001_campaign_creation()
    test_002_audience_builder()
    test_003_forecast()
    test_004_export()
    test_005_campaign_report_import()
    test_006_dashboard_update()
    test_007_learning()
    test_008_revenue_calculation()
    test_campaign_detail_api()
    print("\nAll Volume 06 acceptance tests passed.")
