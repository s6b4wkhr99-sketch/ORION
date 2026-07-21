"""Volume 17 Section 17 — Trend analysis."""

from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.campaign import Campaign, CampaignState
from app.models.learning import CampaignLearning
from app.models.v16_schema import UploadHistory


def _period_key(dt, period: str) -> str:
    if not dt:
        return "unknown"
    if period == "year":
        return str(dt.year)
    if period == "quarter":
        return f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"
    return f"{dt.year}-{dt.month:02d}"


def get_trend_analysis(db: Session, metric: str = "revenue", period: str = "month") -> dict:
    metric = metric.lower()
    period = period.lower()
    trends: dict[str, dict] = defaultdict(lambda: {
        "revenue": 0.0, "customers": 0, "campaigns": 0, "conversion": 0.0, "roi": [], "learning": [],
    })

    for upload in db.query(UploadHistory).all():
        key = _period_key(upload.created_at, period)
        trends[key]["customers"] += upload.customer_count or 0

    for camp in db.query(Campaign).all():
        key = _period_key(camp.start_date or camp.created_at, period)
        trends[key]["campaigns"] += 1

    for row in db.query(CampaignState).all():
        camp = db.query(Campaign).filter(Campaign.campaign_id == row.campaign_id).first()
        key = _period_key(camp.start_date if camp else None, period)
        trends[key]["revenue"] += row.revenue or 0
        if row.roi is not None:
            trends[key]["roi"].append(row.roi)
        if row.sent and row.conversion is not None:
            trends[key]["conversion"] += row.conversion

    for learn in db.query(CampaignLearning).all():
        key = _period_key(learn.campaign_date or learn.created_at, period)
        if learn.learning_score is not None:
            trends[key]["learning"].append(learn.learning_score)

    series = []
    for key in sorted(trends.keys()):
        bucket = trends[key]
        roi_vals = bucket["roi"]
        learn_vals = bucket["learning"]
        point = {
            "period": key,
            "revenue": round(bucket["revenue"], 2),
            "customers": bucket["customers"],
            "campaigns": bucket["campaigns"],
            "conversion": round(bucket["conversion"], 4),
            "roi": round(sum(roi_vals) / len(roi_vals), 4) if roi_vals else None,
            "learning_score": round(sum(learn_vals) / len(learn_vals), 2) if learn_vals else None,
        }
        series.append(point)

    metric_map = {
        "revenue": "revenue",
        "customer": "customers",
        "customers": "customers",
        "campaign": "campaigns",
        "campaigns": "campaigns",
        "forecast": "revenue",
        "conversion": "conversion",
        "roi": "roi",
        "learning": "learning_score",
    }
    selected = metric_map.get(metric, "revenue")

    return {
        "metric": metric,
        "period": period,
        "selected_field": selected,
        "series": series,
        "trends_available": ["revenue", "customer", "campaign", "forecast", "conversion", "roi", "learning"],
    }
