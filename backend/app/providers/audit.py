"""Volume 15 Section 18 — Provider integration audit records."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.security.audit import record_audit


def log_provider_audit(
    db: Session,
    *,
    action: str,
    provider: str,
    campaign_id: str | None = None,
    export_id: str | None = None,
    import_id: str | None = None,
    user_id: str | None = None,
    role: str | None = None,
    customer_count: int = 0,
    status: str = "success",
    duration_ms: float = 0.0,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    ip_address: str | None = None,
    browser: str | None = None,
) -> dict:
    payload = {
        "provider": provider,
        "campaignId": campaign_id,
        "exportId": export_id,
        "importId": import_id,
        "customerCount": customer_count,
        "durationMs": duration_ms,
        "errors": errors or [],
        "warnings": warnings or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    entity_id = export_id or import_id or campaign_id
    record_audit(
        db,
        action=action,
        user_id=user_id,
        role=role,
        entity_type="provider_integration",
        entity_id=entity_id,
        after_value=payload,
        status=status,
        duration_ms=duration_ms,
        ip_address=ip_address,
        browser=browser,
    )
    return payload
