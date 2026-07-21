"""Volume 17 Sections 4–11 — Unified executive intelligence dashboard."""

from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.analytics.filters import AnalyticsFilters
from app.analytics.kpi import build_kpi_library, kpi_with_rule
from app.campaign.analytics import get_customer_distribution, get_executive_summary
from app.campaign.dashboards import PRODUCTS, get_product_dashboard, get_roi_dashboard, get_state_dashboard
from app.campaign.forecast import forecast_accuracy
from app.intelligence.forecasting import le_frame_incentive
from app.models.campaign import Campaign, CampaignState
from app.models.customer import Customer, CustomerIntelligence
from app.models.learning import CampaignLearning
from app.models.v16_schema import UploadHistory


def _campaign_metrics(db: Session, filters: AnalyticsFilters) -> dict:
    q = db.query(Campaign)
    if filters.campaign_type:
        q = q.filter(Campaign.campaign_type == filters.campaign_type)
    if filters.provider:
        q = q.filter(Campaign.provider == filters.provider)
    campaigns = q.all()
    completed = [c for c in campaigns if (c.status or "").lower() in {"completed", "closed", "done"}]
    success_rate = round(len(completed) / len(campaigns), 4) if campaigns else None

    state_rows = db.query(CampaignState).all()
    if filters.campaign_id:
        state_rows = [r for r in state_rows if r.campaign_id == filters.campaign_id]
    actual_revenue = sum(r.revenue or 0 for r in state_rows)
    actual_cost = sum(r.cost or 0 for r in state_rows)
    forecast_rev = sum(c.forecast_revenue or 0 for c in campaigns) or None
    roi = round((actual_revenue - actual_cost) / actual_cost, 4) if actual_cost else None
    sent = sum(r.sent for r in state_rows)
    conversions = sum(r.conversion or 0 for r in state_rows)
    avg_conversion = round(conversions / sent, 6) if sent else None

    learning_rows = db.query(CampaignLearning).all()
    fa_values = [r.forecast_accuracy for r in learning_rows if r.forecast_accuracy is not None]
    ls_values = [r.learning_score for r in learning_rows if r.learning_score is not None]
    forecast_accuracy_avg = round(sum(fa_values) / len(fa_values), 4) if fa_values else None
    learning_score_avg = round(sum(ls_values) / len(ls_values), 2) if ls_values else None

    return {
        "campaign_count": len(campaigns),
        "campaign_success_rate": success_rate,
        "actual_revenue": round(actual_revenue, 2),
        "forecast_revenue": round(forecast_rev, 2) if forecast_rev else None,
        "revenue_gap": round(actual_revenue - (forecast_rev or actual_revenue), 2) if forecast_rev else 0,
        "roi": roi,
        "average_conversion": avg_conversion,
        "forecast_accuracy": forecast_accuracy_avg,
        "learning_score": learning_score_avg,
        "by_type": dict(Counter(c.campaign_type or "Unknown" for c in campaigns)),
        "by_status": dict(Counter(c.status or "Unknown" for c in campaigns)),
        "by_provider": dict(Counter(c.provider or "Unknown" for c in campaigns)),
    }


def _customer_growth(db: Session) -> float | None:
    rows = db.query(UploadHistory).order_by(UploadHistory.created_at.asc()).all()
    if len(rows) < 2:
        return None
    first, last = rows[0], rows[-1]
    if not first.customer_count:
        return None
    return round((last.customer_count - first.customer_count) / first.customer_count, 4)


def _revenue_intelligence(db: Session, filters: AnalyticsFilters, executive: dict, campaign: dict) -> dict:
    expected = executive.get("expected_revenue") or 0
    actual = campaign.get("actual_revenue") or 0
    return {
        "expected_revenue": expected,
        "actual_revenue": actual,
        "revenue_gap": round(actual - expected, 2),
        "revenue_growth": _customer_growth(db),
        "revenue_by_product": executive.get("product_ranking", []),
        "revenue_by_state": executive.get("revenue_by_state", []),
        "revenue_by_segment": executive.get("revenue_by_segment", []),
        "average_revenue_per_customer": round(expected / max(executive.get("total_customers") or 1, 1), 2),
        "le_frame_incentive": executive.get("le_frame_incentive"),
    }


def _geographic_intelligence(db: Session, filters: AnalyticsFilters) -> dict:
    state_dash = get_state_dashboard(db, filters.upload_id, filters.state)
    roi_dash = get_roi_dashboard(db)
    state_rows = db.query(CampaignState).all()
    by_state_campaign: dict[str, int] = defaultdict(int)
    by_state_conversion: dict[str, list[float]] = defaultdict(list)
    for row in state_rows:
        st = row.state or "Unknown"
        by_state_campaign[st] += 1
        if row.sent and row.conversion is not None:
            by_state_conversion[st].append(row.conversion / row.sent)

    top_states = sorted(
        state_dash.get("state_heatmap", []),
        key=lambda x: x.get("revenue") or 0,
        reverse=True,
    )[:10]
    top_zips = sorted(
        state_dash.get("zip_opportunity", []),
        key=lambda x: x.get("expected_revenue") or 0,
        reverse=True,
    )[:10]

    return {
        "revenue_by_state": state_dash.get("state_heatmap", []),
        "revenue_by_zip": state_dash.get("zip_opportunity", []),
        "campaign_by_state": [{"state": k, "campaigns": v} for k, v in sorted(by_state_campaign.items())],
        "conversion_by_state": [
            {"state": k, "conversion": round(sum(v) / len(v), 6) if v else None}
            for k, v in sorted(by_state_conversion.items())
        ],
        "top_revenue_states": top_states,
        "top_revenue_zips": top_zips,
        "roi_by_state": roi_dash.get("roi_chart", [])[:20],
    }


def _product_intelligence(db: Session, filters: AnalyticsFilters) -> dict:
    product_dash = get_product_dashboard(db, filters.upload_id, filters.product)
    items = []
    for product in PRODUCTS:
        dash = get_product_dashboard(db, filters.upload_id, product)
        kpis = dash.get("kpis", {})
        items.append({
            "product": product,
            "target_customers": kpis.get("target_customers"),
            "revenue": kpis.get("expected_revenue"),
            "conversion": kpis.get("average_conversion"),
            "roi": kpis.get("campaign_roi"),
            "forecast_accuracy": kpis.get("forecast_accuracy"),
        })
    return {"products": items, "selected": product_dash}


def _forecast_intelligence(db: Session, campaign: dict, executive: dict) -> dict:
    campaigns = db.query(Campaign).all()
    forecast_revenue = sum(c.forecast_revenue or 0 for c in campaigns)
    forecast_orders = sum(c.forecast_orders or 0 for c in campaigns)
    actual_revenue = campaign.get("actual_revenue") or 0
    accuracy = forecast_accuracy(actual_revenue, forecast_revenue or executive.get("expected_revenue") or 0)
    return {
        "forecast_revenue": round(forecast_revenue, 2) if forecast_revenue else executive.get("expected_revenue"),
        "forecast_orders": round(forecast_orders, 2) if forecast_orders else executive.get("expected_orders"),
        "forecast_roi": campaign.get("roi"),
        "forecast_accuracy": campaign.get("forecast_accuracy") or accuracy,
        "forecast_confidence": round(min(1.0, (accuracy or 0.5) + 0.25), 4) if accuracy else 0.65,
        "forecast_trend": "stable",
    }


def _drill_down_paths(filters: AnalyticsFilters) -> dict:
    base = "/api/v1"
    return {
        "executive": f"{base}/analytics/executive",
        "state": f"{base}/dashboard/state" + (f"?state={filters.state}" if filters.state else ""),
        "zip": f"{base}/dashboard/zip" + (f"?zip={filters.zip_code}" if filters.zip_code else ""),
        "campaign": f"{base}/dashboard/campaigns" + (f"?campaign_id={filters.campaign_id}" if filters.campaign_id else ""),
        "customer": f"{base}/customers",
        "individual_customer": f"{base}/customers/{{customer_id}}",
    }


def get_executive_intelligence(db: Session, filters: AnalyticsFilters | None = None) -> dict:
    filters = filters or AnalyticsFilters()
    executive = get_executive_summary(db, filters.upload_id)
    distribution = get_customer_distribution(db, filters.upload_id)
    campaign = _campaign_metrics(db, filters)

    kpi_values = {
        "total_customers": executive.get("total_customers"),
        "target_customers": executive.get("targetable_customers"),
        "campaigns": campaign["campaign_count"],
        "campaign_success_rate": campaign["campaign_success_rate"],
        "forecast_accuracy": campaign["forecast_accuracy"],
        "expected_revenue": executive.get("expected_revenue"),
        "actual_revenue": campaign["actual_revenue"],
        "revenue_gap": campaign["revenue_gap"],
        "roi": campaign["roi"] or executive.get("campaign_roi"),
        "average_conversion": campaign["average_conversion"],
        "le_frame_incentive": executive.get("le_frame_incentive"),
        "customer_growth": _customer_growth(db),
        "average_order_value": round(
            (executive.get("expected_revenue") or 0) / max(executive.get("expected_orders") or 1, 0.01), 2
        ),
        "campaign_conversion": campaign["average_conversion"],
        "learning_score": campaign["learning_score"],
    }

    seg_q = db.query(CustomerIntelligence).join(Customer)
    if filters.upload_id:
        import uuid
        seg_q = seg_q.filter(Customer.upload_id == uuid.UUID(filters.upload_id))
    segments = seg_q.all()
    message_dist = dict(Counter(s.message_direction or "Unknown" for s in segments))
    product_dist = dict(Counter(s.recommended_product or "Unknown" for s in segments))

    return {
        "executive_kpi": [kpi_with_rule(k, v) for k, v in kpi_values.items()],
        "kpi_library": build_kpi_library(kpi_values),
        "customer_intelligence": {
            "customer_growth": kpi_values["customer_growth"],
            "segment_distribution": distribution.get("ceragem_distribution", {}),
            "prizm_distribution": distribution.get("prizm_distribution", {}),
            "purchase_power_distribution": dict(Counter(
                "High" if (s.purchase_power_index or 0) >= 0.75 else "Medium" if (s.purchase_power_index or 0) >= 0.45 else "Low"
                for s in segments
            )),
            "pain_index_distribution": dict(Counter(
                "High" if (s.pain_index or 0) >= 0.75 else "Medium" if (s.pain_index or 0) >= 0.45 else "Low"
                for s in segments
            )),
            "lifestyle_distribution": dict(Counter(
                "High" if (s.lifestyle_index or 0) >= 0.75 else "Medium" if (s.lifestyle_index or 0) >= 0.45 else "Low"
                for s in segments
            )),
            "message_direction_distribution": message_dist,
            "recommended_product_distribution": product_dist,
            "state_distribution": distribution.get("by_state", []),
            "zip_distribution": distribution.get("by_zip", [])[:50],
        },
        "campaign_intelligence": campaign,
        "revenue_intelligence": _revenue_intelligence(db, filters, executive, campaign),
        "geographic_intelligence": _geographic_intelligence(db, filters),
        "product_intelligence": _product_intelligence(db, filters),
        "forecast_intelligence": _forecast_intelligence(db, campaign, executive),
        "filters_applied": filters.__dict__,
        "drill_down": _drill_down_paths(filters),
        "chart_types_supported": [
            "line", "bar", "stacked_bar", "area", "donut", "heatmap", "treemap", "scatter", "ranking_table", "geo_map",
        ],
    }
