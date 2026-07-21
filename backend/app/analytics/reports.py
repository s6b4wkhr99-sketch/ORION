"""Volume 17 Sections 18–19 — Executive report generation."""

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.analytics.executive import get_executive_intelligence
from app.analytics.filters import AnalyticsFilters
from app.analytics.insights import generate_business_insights
from app.analytics.recommendations import generate_executive_recommendations
from app.config import settings
from app.models.analytics import AnalyticsReport


REPORT_TYPES = frozenset({
    "daily_executive",
    "weekly_campaign",
    "monthly_executive",
    "quarterly_business_review",
    "annual_business_review",
})

FREQUENCIES = frozenset({"daily", "weekly", "monthly", "quarterly", "yearly"})
FORMATS = frozenset({"csv", "json", "excel", "pdf"})


def _reports_dir() -> Path:
    path = Path(settings.upload_dir) / "analytics_reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _build_report_payload(db: Session, report_type: str, filters: AnalyticsFilters) -> dict:
    return {
        "report_type": report_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "executive": get_executive_intelligence(db, filters),
        "insights": generate_business_insights(db, filters),
        "recommendations": generate_executive_recommendations(db, filters),
    }


def _write_csv(payload: dict, path: Path) -> None:
    kpis = payload["executive"]["executive_kpi"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["key", "value", "business_rule_id"])
        for row in kpis:
            writer.writerow([row["key"], row["value"], row.get("business_rule_id")])
        writer.writerow([])
        writer.writerow(["insight", "value", "detail"])
        for insight in payload["insights"]:
            writer.writerow([insight["title"], insight["value"], insight["detail"]])


def generate_executive_report(
    db: Session,
    *,
    report_type: str = "daily_executive",
    frequency: str = "daily",
    output_format: str = "csv",
    filters: AnalyticsFilters | None = None,
    created_by: str | None = None,
) -> AnalyticsReport:
    if report_type not in REPORT_TYPES:
        raise ValueError(f"Unsupported report type: {report_type}")
    if frequency not in FREQUENCIES:
        raise ValueError(f"Unsupported frequency: {frequency}")
    fmt = output_format.lower()
    if fmt not in FORMATS:
        raise ValueError(f"Unsupported format: {output_format}")

    filters = filters or AnalyticsFilters()
    payload = _build_report_payload(db, report_type, filters)
    report_id = uuid.uuid4()
    filename = f"{report_type}_{report_id.hex[:8]}.{ 'json' if fmt in {'json', 'excel', 'pdf'} else 'csv'}"
    file_path = _reports_dir() / filename

    if fmt == "csv" or fmt in {"excel", "pdf"}:
        _write_csv(payload, file_path)
        if fmt in {"excel", "pdf"}:
            payload_path = file_path.with_suffix(".json")
            payload_path.write_text(json.dumps(payload, default=str), encoding="utf-8")
    else:
        file_path.write_text(json.dumps(payload, default=str, indent=2), encoding="utf-8")

    row = AnalyticsReport(
        report_id=report_id,
        report_type=report_type,
        frequency=frequency,
        output_format=fmt,
        file_name=filename,
        file_path=str(file_path),
        status="completed",
        created_by=created_by,
        summary_json=json.dumps({
            "kpi_count": len(payload["executive"]["executive_kpi"]),
            "insight_count": len(payload["insights"]),
            "recommendation_count": len(payload["recommendations"]),
        }),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_report(db: Session, report_id: str) -> AnalyticsReport | None:
    try:
        rid = uuid.UUID(report_id)
    except ValueError:
        return None
    return db.query(AnalyticsReport).filter(AnalyticsReport.report_id == rid).first()


def list_reports(db: Session, limit: int = 20) -> list[dict]:
    rows = db.query(AnalyticsReport).order_by(AnalyticsReport.created_at.desc()).limit(limit).all()
    return [{
        "report_id": str(r.report_id),
        "report_type": r.report_type,
        "frequency": r.frequency,
        "output_format": r.output_format,
        "file_name": r.file_name,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "summary": json.loads(r.summary_json) if r.summary_json else {},
    } for r in rows]


def export_analytics_csv(db: Session, filters: AnalyticsFilters | None = None) -> str:
    filters = filters or AnalyticsFilters()
    payload = _build_report_payload(db, "daily_executive", filters)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["key", "value"])
    for row in payload["executive"]["executive_kpi"]:
        writer.writerow([row["key"], row["value"]])
    return buffer.getvalue()
