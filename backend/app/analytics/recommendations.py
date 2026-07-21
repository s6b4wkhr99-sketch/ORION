"""Volume 17 Section 15 — Executive Recommendation Engine."""

from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.analytics.filters import AnalyticsFilters
from app.analytics.insights import generate_business_insights
from app.campaign.analytics import get_executive_summary
from app.campaign.dashboards import PRODUCTS, get_state_dashboard
from app.models.campaign import Campaign, CampaignState
from app.models.customer import Customer, CustomerIntelligence
from app.models.learning import CampaignLearning, LearningCampaign


def _recommendation(category: str, action: str, target, rationale: str, confidence: float) -> dict:
    return {
        "category": category,
        "action": action,
        "target": target,
        "rationale": rationale,
        "confidence_score": round(confidence, 4),
    }


def generate_executive_recommendations(db: Session, filters: AnalyticsFilters | None = None) -> list[dict]:
    filters = filters or AnalyticsFilters()
    executive = get_executive_summary(db, filters.upload_id)
    state_dash = get_state_dashboard(db, filters.upload_id)
    insights = generate_business_insights(db, filters)
    recs: list[dict] = []

    learning = db.query(LearningCampaign).order_by(LearningCampaign.score.desc()).first()
    if learning and learning.recommendation:
        recs.append(_recommendation(
            "campaign",
            "Execute follow-up campaign",
            learning.campaign_id,
            learning.recommendation,
            (learning.score or 50) / 100,
        ))

    type_perf: dict[str, list[float]] = defaultdict(list)
    for camp in db.query(Campaign).all():
        rows = db.query(CampaignState).filter(CampaignState.campaign_id == camp.campaign_id).all()
        rois = [r.roi for r in rows if r.roi is not None]
        if rois:
            type_perf[camp.campaign_type or "Email"].append(sum(rois) / len(rois))
    if type_perf:
        best_type = max(type_perf, key=lambda t: sum(type_perf[t]) / len(type_perf[t]))
        recs.append(_recommendation(
            "campaign_type",
            "Next Campaign Type",
            best_type,
            f"{best_type} campaigns show the strongest historical ROI.",
            0.78,
        ))

    top_product = executive.get("top_product_opportunity") or PRODUCTS[0]
    recs.append(_recommendation(
        "product",
        "Next Product",
        top_product,
        f"Intelligence ranks {top_product} as the top revenue opportunity.",
        0.82,
    ))

    top_state = executive.get("top_performing_state")
    if top_state:
        recs.append(_recommendation(
            "state",
            "Next State",
            top_state,
            f"Prioritize {top_state} for the next campaign wave based on expected revenue.",
            0.85,
        ))

    zip_rows = state_dash.get("zip_opportunity") or []
    if zip_rows:
        top_zip = max(zip_rows, key=lambda r: r.get("expected_revenue") or 0)
        recs.append(_recommendation(
            "zip",
            "Next ZIP",
            top_zip.get("zip"),
            f"ZIP {top_zip.get('zip')} offers the highest localized revenue potential.",
            0.8,
        ))

    segments = db.query(CustomerIntelligence).join(Customer).all()
    if segments:
        seg_rev: dict[str, float] = defaultdict(float)
        for s in segments:
            seg_rev[s.ceragem_segment or "Unknown"] += s.expected_revenue or 0
        best_seg = max(seg_rev, key=seg_rev.get)
        recs.append(_recommendation(
            "segment",
            "Next Customer Segment",
            best_seg,
            f"Segment {best_seg} contributes the most expected revenue.",
            0.83,
        ))

        msg_rev: dict[str, float] = defaultdict(float)
        for s in segments:
            msg_rev[s.message_direction or "Unknown"] += s.expected_revenue or 0
        best_msg = max(msg_rev, key=msg_rev.get)
        recs.append(_recommendation(
            "message",
            "Next Message Direction",
            best_msg,
            f"Lead with '{best_msg}' messaging for highest conversion potential.",
            0.77,
        ))

    cl = db.query(CampaignLearning).order_by(CampaignLearning.learning_score.desc()).first()
    budget_hint = round((cl.revenue or executive.get("expected_revenue") or 10000) * 0.15, 2) if cl else round(
        (executive.get("expected_revenue") or 0) * 0.12, 2
    )
    recs.append(_recommendation(
        "budget",
        "Next Budget Allocation",
        budget_hint,
        "Allocate budget proportional to top-state revenue opportunity and historical ROI.",
        0.7,
    ))

    for insight in insights[:2]:
        recs.append(_recommendation(
            "strategic",
            f"Address: {insight['title']}",
            insight["value"],
            insight["detail"],
            0.65,
        ))

    return recs
