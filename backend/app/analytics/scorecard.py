"""Volume 17 Section 25 — Executive scorecard."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analytics.executive import get_executive_intelligence
from app.analytics.filters import AnalyticsFilters
from app.analytics.learning_intel import get_learning_intelligence
from app.devops.health import build_health_payload
from app.models.campaign import CampaignReportUpload
from app.models.export import ExportJob
from app.models.raw import RawUpload


def _score(value: float | None, threshold: float, invert: bool = False) -> tuple[str, float]:
    if value is None:
        return "unknown", 50.0
    passed = value >= threshold if not invert else value <= threshold
    normalized = min(100.0, max(0.0, (value if not invert else (1 - value)) * 100))
    return ("healthy" if passed else "at_risk"), round(normalized, 1)


def get_executive_scorecard(db: Session, filters: AnalyticsFilters | None = None) -> dict:
    filters = filters or AnalyticsFilters()
    executive = get_executive_intelligence(db, filters)
    learning = get_learning_intelligence(db)
    health = build_health_payload()

    kpi_map = {k["key"]: k["value"] for k in executive["executive_kpi"]}
    roi = kpi_map.get("roi")
    forecast_acc = kpi_map.get("forecast_accuracy")
    revenue_gap = abs(kpi_map.get("revenue_gap") or 0)
    customer_growth = kpi_map.get("customer_growth")

    camp_status, camp_score = _score(roi, 0.5)
    forecast_status, forecast_score = _score(forecast_acc, 0.7)
    revenue_status, revenue_score = _score(revenue_gap, 50000, invert=True)
    if customer_growth is not None:
        customer_status, customer_score = _score(customer_growth, 0)
    else:
        customer_status, customer_score = "stable", 70.0
    learning_status, learning_score_val = _score(learning.get("learning_score"), 55)

    dimensions = {
        "platform_health": {
            "status": "healthy" if health["application"]["status"] == "up" else "degraded",
            "score": 95.0 if health["application"]["status"] == "up" else 40.0,
        },
        "campaign_health": {"status": camp_status, "score": camp_score},
        "forecast_health": {"status": forecast_status, "score": forecast_score},
        "revenue_health": {"status": revenue_status, "score": revenue_score},
        "customer_health": {"status": customer_status, "score": customer_score},
        "learning_health": {"status": learning_status, "score": learning_score_val},
        "provider_health": {
            "status": "healthy",
            "score": 85.0,
        },
        "dashboard_health": {
            "status": "healthy" if health["database"]["status"] == "up" else "degraded",
            "score": 90.0 if health["database"]["status"] == "up" else 35.0,
        },
    }

    failed_imports = db.query(func.count(CampaignReportUpload.id)).filter(CampaignReportUpload.status == "failed").scalar() or 0
    failed_exports = db.query(func.count(ExportJob.export_id)).filter(ExportJob.download_url.is_(None)).scalar() or 0
    pending_uploads = db.query(func.count(RawUpload.upload_id)).filter(RawUpload.status == "failed").scalar() or 0

    if failed_imports:
        dimensions["provider_health"] = {"status": "at_risk", "score": max(30.0, 85 - failed_imports * 10)}
    if failed_exports:
        dimensions["campaign_health"]["status"] = "at_risk"
        dimensions["campaign_health"]["score"] = min(dimensions["campaign_health"]["score"], 60.0)

    scores = [d["score"] for d in dimensions.values() if isinstance(d.get("score"), (int, float))]
    overall = round(sum(scores) / len(scores), 1) if scores else 50.0

    return {
        "dimensions": dimensions,
        "overall_business_score": overall,
        "overall_status": "healthy" if overall >= 70 else "at_risk" if overall >= 50 else "critical",
        "operational_flags": {
            "failed_imports": failed_imports,
            "failed_exports": failed_exports,
            "failed_uploads": pending_uploads,
        },
    }
