"""Volume 06 Section 23 — Immutable campaign learning records."""

import json
import uuid
from collections import Counter
from datetime import date

from sqlalchemy.orm import Session

from app.campaign.forecast import forecast_accuracy
from app.models.campaign import Campaign, CampaignProduct, CampaignState
from app.models.customer import Customer, CustomerIntelligence
from app.models.learning import CampaignLearning


def _aggregate_distributions(db: Session, state_rows: list[CampaignState]) -> tuple[dict, dict, dict, dict]:
    states = {r.state for r in state_rows if r.state}
    q = db.query(Customer, CustomerIntelligence).join(
        CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id
    )
    if states:
        q = q.filter(Customer.state.in_(states))
    rows = q.all()

    ceragem = Counter(i.ceragem_segment or "Unknown" for _, i in rows)
    prizm = Counter(i.prizm_proxy_segment or "Unknown" for _, i in rows)
    product = Counter(i.recommended_product or "Unknown" for _, i in rows)
    message = Counter(i.message_direction or "Unknown" for _, i in rows)
    return dict(ceragem), dict(prizm), dict(product), dict(message)


def create_campaign_learning_record(
    db: Session,
    report_id: uuid.UUID,
    campaign: Campaign,
    state_rows: list[CampaignState],
    product_rows: list[CampaignProduct],
    expected_revenue: float | None = None,
) -> CampaignLearning | None:
    """
    Create one immutable learning record per campaign (Section 23.5).
    No updates permitted after creation.
    """
    campaign_states = [r for r in state_rows if r.campaign_id == campaign.campaign_id]
    if not campaign_states:
        return None

    sent = sum(r.sent for r in campaign_states)
    opened = sum(r.open for r in campaign_states)
    clicked = sum(r.click for r in campaign_states)
    revenue = sum(r.revenue or 0 for r in campaign_states)
    cost = sum(r.cost or 0 for r in campaign_states)
    orders = sum(r.conversion or 0 for r in campaign_states) or round(clicked * 0.02, 2)
    roi = round((revenue - cost) / cost, 4) if cost else None
    ctr = round(clicked / sent, 4) if sent else None
    ctor = round(clicked / opened, 4) if opened else None
    conversion = round(orders / sent, 6) if sent else None
    accuracy = forecast_accuracy(revenue, expected_revenue or revenue)

    ceragem, prizm, product, message = _aggregate_distributions(db, campaign_states)
    score = round(min(100, (accuracy or 0.5) * 40 + (roi or 0) * 10 + (ctr or 0) * 200), 2)

    record = CampaignLearning(
        campaign_id=campaign.campaign_id,
        campaign_type=campaign.campaign_type,
        campaign_date=campaign.start_date or date.today(),
        audience_count=sent,
        ceragem_segment_distribution=json.dumps(ceragem),
        prizm_distribution=json.dumps(prizm),
        product_distribution=json.dumps(product),
        message_direction=json.dumps(message),
        provider=campaign.provider,
        revenue=round(revenue, 2),
        roi=roi,
        ctr=ctr,
        ctor=ctor,
        orders=orders,
        conversion=conversion,
        forecast_accuracy=accuracy,
        learning_score=score,
        source_report_id=report_id,
    )
    db.add(record)
    return record


def create_learning_records_for_report(
    db: Session,
    report_id: uuid.UUID,
    campaigns: dict[str, Campaign],
    state_rows: list[CampaignState],
    product_rows: list[CampaignProduct],
) -> int:
    created = 0
    for campaign in campaigns.values():
        if create_campaign_learning_record(db, report_id, campaign, state_rows, product_rows):
            created += 1
    return created
