"""Layer 05 — Learning Database from campaign performance."""

import uuid

from sqlalchemy.orm import Session

from app.models.campaign import CampaignProduct, CampaignState
from app.models.learning import LearningCampaign


def _summary(state_row: CampaignState, campaign_name: str) -> str:
    state = state_row.state or "National"
    open_pct = f"{(state_row.open_rate or 0) * 100:.1f}%"
    ctr_pct = f"{(state_row.ctr or 0) * 100:.2f}%"
    revenue = f"${state_row.revenue:,.0f}" if state_row.revenue else "N/A"
    return f"{state} — {campaign_name}: {state_row.sent:,} sent, {open_pct} open, {ctr_pct} CTR, revenue {revenue}."


def _recommendation(state_row: CampaignState, product: str | None) -> str:
    state = state_row.state or "target states"
    if state_row.roi and state_row.roi > 1:
        return f"Repeat campaign in {state} with {product or 'top product'} — strong ROI."
    if state_row.ctr and state_row.ctr >= 0.03:
        return f"High CTR in {state}. Scale with premium message and consultation CTA."
    if state_row.open_rate and state_row.open_rate < 0.15:
        return f"Low open rate in {state}. Revise subject line before next send."
    return f"Refine segment and message mix for {state} next campaign."


def generate_learning_records(
    db: Session,
    report_id: uuid.UUID,
    state_rows: list[CampaignState],
    product_rows: list[CampaignProduct],
) -> int:
    product_by_campaign: dict[str, str] = {}
    for row in product_rows:
        if row.product and row.campaign_id:
            product_by_campaign.setdefault(row.campaign_id, row.product)

    records: list[LearningCampaign] = []
    for row in state_rows:
        product = product_by_campaign.get(row.campaign_id)
        score = min(1.0, 0.4 + (row.ctr or 0) * 5 + (row.roi or 0) * 0.1)
        records.append(LearningCampaign(
            campaign_id=row.campaign_id,
            product=product,
            state=row.state,
            result=f"sent={row.sent}, open={row.open}, click={row.click}, revenue={row.revenue}",
            score=round(score, 4),
            insight_summary=_summary(row, row.campaign_id),
            recommendation=_recommendation(row, product),
            sent=row.sent,
            open=row.open,
            click=row.click,
            revenue=row.revenue,
            roi=row.roi,
            source_report_id=report_id,
        ))

    db.add_all(records)
    return len(records)
