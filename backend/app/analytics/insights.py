"""Volume 17 Section 14 — Business Insight Engine."""

from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.analytics.filters import AnalyticsFilters
from app.campaign.analytics import get_executive_summary
from app.campaign.dashboards import get_state_dashboard
from app.models.campaign import Campaign, CampaignState
from app.models.customer import Customer, CustomerIntelligence


def _insight(category: str, title: str, value, detail: str, metric: str) -> dict:
    return {
        "category": category,
        "title": title,
        "value": value,
        "detail": detail,
        "metric": metric,
    }


def generate_business_insights(db: Session, filters: AnalyticsFilters | None = None) -> list[dict]:
    filters = filters or AnalyticsFilters()
    executive = get_executive_summary(db, filters.upload_id)
    state_dash = get_state_dashboard(db, filters.upload_id, filters.state)
    insights: list[dict] = []

    top_state = executive.get("top_performing_state")
    if top_state:
        insights.append(_insight(
            "geographic",
            "Highest Performing State",
            top_state,
            f"{top_state} leads expected revenue across the customer base.",
            "expected_revenue",
        ))

    zip_rows = state_dash.get("zip_opportunity") or []
    if zip_rows:
        top_zip = max(zip_rows, key=lambda r: r.get("expected_revenue") or 0)
        insights.append(_insight(
            "geographic",
            "Highest Revenue ZIP",
            top_zip.get("zip"),
            f"ZIP {top_zip.get('zip')} ({top_zip.get('city', '—')}) shows strongest revenue potential.",
            "expected_revenue",
        ))

    top_product = executive.get("top_product_opportunity")
    if top_product:
        insights.append(_insight(
            "product",
            "Best Performing Product",
            top_product,
            f"{top_product} is the top revenue opportunity in current intelligence.",
            "recommended_product",
        ))

    seg_q = db.query(CustomerIntelligence).join(Customer)
    segments = seg_q.all()
    if segments:
        seg_counts = Counter(s.ceragem_segment or "Unknown" for s in segments)
        fastest = seg_counts.most_common(1)[0][0] if seg_counts else None
        if fastest:
            insights.append(_insight(
                "customer",
                "Most Active Customer Segment",
                fastest,
                f"Segment {fastest} has the largest targetable audience.",
                "customer_count",
            ))

        pp_segments: dict[str, list[float]] = defaultdict(list)
        for s in segments:
            pp_segments[s.ceragem_segment or "Unknown"].append(s.purchase_power_index or 0)
        if pp_segments:
            best_pp = max(pp_segments, key=lambda k: sum(pp_segments[k]) / len(pp_segments[k]))
            insights.append(_insight(
                "customer",
                "Highest Purchase Power Segment",
                best_pp,
                f"Segment {best_pp} shows the highest average purchase power index.",
                "purchase_power_index",
            ))

        msg_rev: dict[str, float] = defaultdict(float)
        for s in segments:
            msg_rev[s.message_direction or "Unknown"] += s.expected_revenue or 0
        if msg_rev:
            best_msg = max(msg_rev, key=msg_rev.get)
            insights.append(_insight(
                "messaging",
                "Most Effective Message Direction",
                best_msg,
                f"Message direction '{best_msg}' drives the highest expected revenue.",
                "expected_revenue",
            ))

    state_rows = db.query(CampaignState).all()
    campaign_roi: dict[str, list[float]] = defaultdict(list)
    for row in state_rows:
        if row.roi is not None:
            campaign_roi[row.campaign_id].append(row.roi)
    if campaign_roi:
        lowest_cid = min(campaign_roi, key=lambda c: sum(campaign_roi[c]) / len(campaign_roi[c]))
        camp = db.query(Campaign).filter(Campaign.campaign_id == lowest_cid).first()
        insights.append(_insight(
            "campaign",
            "Lowest ROI Campaign",
            camp.campaign_name if camp else lowest_cid,
            f"Campaign {lowest_cid} underperforms on ROI — review targeting and message fit.",
            "roi",
        ))

    prizm_counts = Counter(s.prizm_proxy_segment or "Unknown" for s in segments)
    if len(prizm_counts) >= 2:
        growing = prizm_counts.most_common(2)
        insights.append(_insight(
            "customer",
            "Fastest Growing Segment",
            growing[0][0],
            f"PRIZM proxy segment {growing[0][0]} shows the largest share of intelligence records.",
            "segment_share",
        ))

    return insights
