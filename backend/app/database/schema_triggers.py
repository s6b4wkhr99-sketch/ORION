"""Volume 16 Section 12 — Schema trigger behaviors (cross-database)."""

import json
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.customer import CustomerIntelligence
from app.models.v16_schema import CampaignReport, Recommendation, UploadHistory


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
    existing = (
        db.query(Recommendation)
        .filter(Recommendation.customer_id == intel.customer_id)
        .order_by(Recommendation.generated_at.desc())
        .first()
    )
    confidence = intel.expected_conversion or 0.0
    if existing and existing.recommended_product == intel.recommended_product:
        existing.confidence_score = confidence
        existing.recommended_message = intel.message_direction
        existing.generated_at = datetime.utcnow()
        return
    db.add(
        Recommendation(
            customer_id=intel.customer_id,
            recommended_product=intel.recommended_product,
            recommended_message=intel.message_direction,
            confidence_score=confidence,
            generated_at=datetime.utcnow(),
        )
    )


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


def stamp_intelligence_generated(intel: CustomerIntelligence, rule_version: str = "1.0.0") -> None:
    intel.generated_at = datetime.utcnow()
    intel.rule_version = rule_version


def update_campaign_actuals(campaign: Campaign, revenue: float | None, orders: float | None) -> None:
    if revenue is not None:
        campaign.actual_revenue = revenue
    if orders is not None:
        campaign.actual_orders = orders
    campaign.updated_at = datetime.utcnow()
    if campaign.status in {"completed", "approved"}:
        campaign.status = "completed"
