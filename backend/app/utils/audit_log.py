"""Volume 08 Section 18 — Audit and operational logging."""

import logging

from app.utils.timezone import now_app_iso

logger = logging.getLogger("cios.audit")


def audit(event: str, **fields) -> None:
    payload = {"event": event, "ts": now_app_iso(), **fields}
    logger.info("%s", payload)


def audit_upload(file_name: str, upload_id: str, status: str, rows: int = 0) -> None:
    audit("upload", file_name=file_name, upload_id=upload_id, status=status, rows=rows)


def audit_mapping(upload_id: str, mapped_columns: int) -> None:
    audit("mapping", upload_id=upload_id, mapped_columns=mapped_columns)


def audit_validation(upload_id: str, valid: bool, warnings: int = 0) -> None:
    audit("validation", upload_id=upload_id, valid=valid, warnings=warnings)


def audit_intelligence(upload_id: str, rows_processed: int) -> None:
    audit("intelligence_generation", upload_id=upload_id, rows_processed=rows_processed)


def audit_campaign(action: str, campaign_id: str, **extra) -> None:
    audit("campaign", action=action, campaign_id=campaign_id, **extra)


def audit_export(export_id: str, provider: str, campaign: str) -> None:
    audit("export", export_id=export_id, provider=provider, campaign=campaign)


def audit_report_import(report_id: str, campaign_id: str | None, rows: int) -> None:
    audit("report_import", report_id=report_id, campaign_id=campaign_id, rows=rows)


def audit_error(context: str, message: str) -> None:
    audit("error", context=context, message=message)
