"""Volume 17 Section 24 — Executive alerts."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analytics.executive import get_executive_intelligence
from app.analytics.filters import AnalyticsFilters
from app.analytics.scorecard import get_executive_scorecard
from app.devops.health import build_health_payload
from app.models.campaign import CampaignReportUpload
from app.models.export import ExportJob


ROI_THRESHOLD = 0.3
FORECAST_ACCURACY_THRESHOLD = 0.6


def _alert(severity: str, message: str, module: str, metric: str | None = None) -> dict:
    return {"severity": severity, "message": message, "module": module, "metric": metric}


def get_executive_alerts(db: Session, filters: AnalyticsFilters | None = None) -> list[dict]:
    filters = filters or AnalyticsFilters()
    executive = get_executive_intelligence(db, filters)
    scorecard = get_executive_scorecard(db, filters)
    health = build_health_payload()
    alerts: list[dict] = []

    kpi_map = {k["key"]: k["value"] for k in executive["executive_kpi"]}
    roi = kpi_map.get("roi")
    if roi is not None and roi < ROI_THRESHOLD:
        alerts.append(_alert("high", f"Campaign ROI ({roi}) below threshold {ROI_THRESHOLD}", "campaign", "roi"))

    forecast_acc = kpi_map.get("forecast_accuracy")
    if forecast_acc is not None and forecast_acc < FORECAST_ACCURACY_THRESHOLD:
        alerts.append(_alert(
            "medium",
            f"Forecast accuracy ({forecast_acc}) decreased below {FORECAST_ACCURACY_THRESHOLD}",
            "forecast",
            "forecast_accuracy",
        ))

    revenue_gap = kpi_map.get("revenue_gap")
    if revenue_gap is not None and revenue_gap < -1000:
        alerts.append(_alert("medium", "Actual revenue trailing forecast — revenue decrease detected", "revenue", "revenue_gap"))

    failed_imports = (
        db.query(func.count(CampaignReportUpload.id))
        .filter(CampaignReportUpload.status == "failed")
        .scalar()
        or 0
    )
    if failed_imports:
        alerts.append(_alert("high", f"{failed_imports} provider import(s) failed", "provider", "import"))

    failed_exports = db.query(ExportJob).filter(ExportJob.download_url.is_(None)).count()
    if failed_exports > 3:
        alerts.append(_alert("medium", f"{failed_exports} campaign export(s) pending or failed", "export", "export"))

    if health["database"]["status"] != "up":
        alerts.append(_alert("critical", "Dashboard refresh / database health degraded", "dashboard", "database"))

    if scorecard["dimensions"]["learning_health"]["status"] == "at_risk":
        alerts.append(_alert("medium", "Learning engine score below target", "learning", "learning_score"))

    return alerts
