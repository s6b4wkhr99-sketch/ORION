"""Volume 07 Section 6 — Campaign API services."""

import uuid

from sqlalchemy.orm import Session

from app.campaign.detail import get_campaign_detail
from app.campaign.forecast import compute_campaign_forecast
from app.models.campaign import Campaign
from app.models.customer import Customer, CustomerIntelligence
from app.schemas.campaign import CampaignCreateRequest, CampaignUpdateRequest
from app.utils.audit_log import audit_campaign

IMMUTABLE_CAMPAIGN_STATUSES = frozenset({"completed", "approved"})


class CampaignImmutableError(Exception):
    pass


def list_campaigns(db: Session) -> list[dict]:
    return [
        {
            "campaignId": c.campaign_id,
            "campaignName": c.campaign_name,
            "campaignType": c.campaign_type,
            "status": c.status,
            "provider": c.provider,
            "startDate": c.start_date.isoformat() if c.start_date else None,
            "endDate": c.end_date.isoformat() if c.end_date else None,
        }
        for c in db.query(Campaign).order_by(Campaign.created_at.desc()).all()
    ]


def create_campaign(db: Session, body: CampaignCreateRequest) -> dict:
    campaign_id = f"CAMP-{uuid.uuid4().hex[:8].upper()}"
    campaign = Campaign(
        campaign_id=campaign_id,
        campaign_name=body.campaignName,
        campaign_type=body.campaignType,
        status="draft",
        provider=body.provider,
        owner="CIOS Admin",
        forecast_version="Volume 06 v1.0",
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    audit_campaign("create", campaign.campaign_id, name=campaign.campaign_name)
    return {
        "campaignId": campaign.campaign_id,
        "campaignName": campaign.campaign_name,
        "status": campaign.status,
    }


def update_campaign(db: Session, campaign_id: str, body: CampaignUpdateRequest) -> dict | None:
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
    if not campaign:
        return None
    if campaign.status in IMMUTABLE_CAMPAIGN_STATUSES:
        raise CampaignImmutableError("Completed campaigns cannot be modified")
    before = {"status": campaign.status, "campaignName": campaign.campaign_name}
    if body.campaignName is not None:
        campaign.campaign_name = body.campaignName
    if body.campaignType is not None:
        campaign.campaign_type = body.campaignType
    if body.status is not None:
        campaign.status = body.status
    if body.budget is not None:
        campaign.budget = body.budget
    if body.provider is not None:
        campaign.provider = body.provider
    db.commit()
    db.refresh(campaign)
    audit_campaign("update", campaign.campaign_id, before=before, after={"status": campaign.status})
    return {
        "campaignId": campaign.campaign_id,
        "campaignName": campaign.campaign_name,
        "status": campaign.status,
    }


def delete_campaign(db: Session, campaign_id: str) -> bool:
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
    if not campaign:
        return False
    if campaign.status in IMMUTABLE_CAMPAIGN_STATUSES:
        raise CampaignImmutableError("Completed campaigns cannot be deleted")
    db.delete(campaign)
    db.commit()
    return True


def get_campaign_audience(db: Session, campaign_id: str) -> dict | None:
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
    if not campaign:
        return None
    rows = db.query(Customer, CustomerIntelligence).join(
        CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id
    ).limit(500).all()
    return {
        "campaignId": campaign_id,
        "targetCustomers": len(rows),
        "preview": [
            {
                "customerId": str(c.customer_id),
                "email": c.email,
                "state": c.state,
                "segment": i.prizm_proxy_segment,
                "product": i.recommended_product,
                "expectedRevenue": i.expected_revenue,
            }
            for c, i in rows[:50]
        ],
    }


def get_campaign_forecast(db: Session, campaign_id: str) -> dict | None:
    detail = get_campaign_detail(db, campaign_id)
    if detail.get("error"):
        return None
    return {
        "campaignId": campaign_id,
        "forecast": detail["forecast"],
        "kpis": detail["kpis"],
        "forecastVsActual": detail["forecast_vs_actual"],
    }


def approve_campaign(db: Session, campaign_id: str, *, approver: str | None = None) -> dict | None:
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
    if not campaign:
        return None
    before_status = campaign.status
    campaign.status = "approved"
    db.commit()
    db.refresh(campaign)
    audit_campaign("approve", campaign.campaign_id, approver=approver, before_status=before_status)
    return {"campaignId": campaign_id, "status": campaign.status, "approved": True}
