"""Volume 11 Section 10 — Persistent immutable audit logging."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog

logger = logging.getLogger("cios.audit")


def record_audit(
    db: Session,
    *,
    action: str,
    user_id: str | None = None,
    role: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    before_value: Any = None,
    after_value: Any = None,
    ip_address: str | None = None,
    browser: str | None = None,
    status: str = "success",
    duration_ms: float | None = None,
) -> AuditLog:
    entry = AuditLog(
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        user_id=user_id,
        role=role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_value=json.dumps(before_value) if before_value is not None else None,
        after_value=json.dumps(after_value) if after_value is not None else None,
        ip_address=ip_address,
        browser=browser,
        status=status,
        duration_ms=duration_ms,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    payload = {
        "audit_id": str(entry.audit_id),
        "action": action,
        "user_id": user_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "status": status,
    }
    logger.info("%s", payload)
    return entry


def list_audit_logs(db: Session, limit: int = 100) -> list[dict]:
    rows = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "auditId": str(r.audit_id),
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "userId": r.user_id,
            "role": r.role,
            "action": r.action,
            "entityType": r.entity_type,
            "entityId": r.entity_id,
            "status": r.status,
        }
        for r in rows
    ]
