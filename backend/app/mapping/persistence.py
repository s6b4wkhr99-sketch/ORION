"""RFC-001 — Persist mapping history and exceptions."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.mapping.rfc_constants import MATCH_UNKNOWN, STATUS_REVIEW
from app.models.auto_mapping import MappingException, MappingHistory


def record_mapping_history(
    db: Session,
    upload_id: str | None,
    file_name: str,
    mapping_report: list[dict],
) -> None:
    for row in mapping_report:
        db.add(MappingHistory(
            upload_id=upload_id,
            file_name=file_name,
            uploaded_header=row["uploaded_header"],
            internal_field=row.get("internal_field"),
            match_type=row["match_type"],
            confidence=float(row.get("confidence", 0)),
            status=row.get("status", "mapped"),
        ))


def record_mapping_exceptions(
    db: Session,
    upload_id: str | None,
    mapping_report: list[dict],
) -> None:
    for row in mapping_report:
        if row["match_type"] == MATCH_UNKNOWN or row.get("status") == STATUS_REVIEW:
            db.add(MappingException(
                upload_id=upload_id,
                uploaded_header=row["uploaded_header"],
                suggestion=row.get("suggestion") or row.get("internal_field"),
                similarity_score=float(row.get("confidence", 0)) or None,
                resolution="ignored" if row["match_type"] == MATCH_UNKNOWN else "review",
            ))
