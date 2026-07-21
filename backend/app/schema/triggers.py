"""Volume 16 Section 12 — Schema trigger behaviors (cross-database)."""

import json
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.customer import CustomerIntelligence
from app.models.v16_schema import CampaignReport, UploadHistory


def record_upload_history(
    db: Session,
    *,
    upload_id: uuid.UUID,
    customer_count: int,
    duplicate_count: int = 0,
    warning_count: int = 0,
    processing_time: float | None = None,
    status: str = "completed",
) -> UploadHistory:
    entry = UploadHistory(
        upload_id=upload_id,
        customer_count=customer_count,
        duplicate_count=duplicate_count,
        warning_count=warning_count,
        processing_time=processing_time,
        status=status,
        created_at=datetime.utcnow(),
    )
    db.add(entry)
    db.flush()
    return entry


def sync_recommendation_from_intelligence(db: Session, intel: CustomerIntelligence) -> None:
    """Volume 18 — persist full AI recommendation from intelligence row."""
    from app.models.customer import Customer

    from app.ai_engine.engine import run_ai_recommendation_for_intelligence

    customer = db.query(Customer).filter(Customer.customer_id == intel.customer_id).first()
    if not customer:
        return
    run_ai_recommendation_for_intelligence(db, customer, intel, generated_by="upload_pipeline")


def record_campaign_report_summary(
    db: Session,
    *,
    campaign_id: str,
    provider: str | None,
    total_sent: int,
    delivered: int,
    opened: int,
    clicked: int,
    unique_click: int,
    ctr: float | None,
    ctor: float | None,
    revenue: float | None,
    conversion: float | None,
) -> CampaignReport:
    report = CampaignReport(
        campaign_id=campaign_id,
        provider=provider,
        total_sent=total_sent,
        delivered=delivered,
        opened=opened,
        clicked=clicked,
        unique_click=unique_click,
        ctr=ctr,
        ctor=ctor,
        revenue=revenue,
        conversion=conversion,
        imported_at=datetime.utcnow(),
    )
    db.add(report)
    db.flush()
    return report


def stamp_intelligence_generated(
    intel: CustomerIntelligence,
    rule_version: str = "Volume 04 Rules 001–070",
    *,
    calculation_version: str | None = None,
    engine_version: str | None = None,
    generated_by: str | None = None,
) -> None:
    from app.intelligence.framework_constants import CALCULATION_VERSION, INTELLIGENCE_ENGINE_VERSION

    intel.generated_at = datetime.utcnow()
    intel.rule_version = rule_version
    intel.calculation_version = calculation_version or CALCULATION_VERSION
    intel.engine_version = engine_version or INTELLIGENCE_ENGINE_VERSION
    if generated_by:
        intel.generated_by = generated_by


def update_campaign_actuals(campaign: Campaign, revenue: float | None, orders: float | None) -> None:
    if revenue is not None:
        campaign.actual_revenue = revenue
    if orders is not None:
        campaign.actual_orders = orders
    campaign.updated_at = datetime.utcnow()
    if campaign.status in {"completed", "approved"}:
        campaign.status = "completed"
