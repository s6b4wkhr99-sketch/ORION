"""RFC-001 — Mapping API service layer."""

from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from app.acquisition.upload import save_upload_file
from app.mapping.auto_engine import generate_mapping_report, validate_mapping
from app.mapping.auto_engine import standardize_mapped_rows
from app.mapping.standardization import standardize_preview
from app.models.auto_mapping import FieldAlias, FieldMaster


def list_field_master(db: Session) -> list[dict]:
    rows = db.query(FieldMaster).order_by(FieldMaster.internal_field).all()
    return [
        {
            "internal_field": r.internal_field,
            "category": r.category,
            "data_type": r.data_type,
            "required": r.required,
            "description": r.description,
        }
        for r in rows
    ]


def list_field_aliases(db: Session, internal_field: str | None = None) -> list[dict]:
    query = db.query(FieldAlias).filter(FieldAlias.approved.is_(True))
    if internal_field:
        query = query.filter(FieldAlias.internal_field == internal_field)
    rows = query.order_by(FieldAlias.alias_header).all()
    return [
        {
            "alias_header": r.alias_header,
            "internal_field": r.internal_field,
            "match_type": r.match_type,
            "confidence": r.confidence,
        }
        for r in rows
    ]


def _load_headers_from_file(file_path: str, file_name: str) -> tuple[list[str], list[dict]]:
    ext = file_name.lower().split(".")[-1]
    if ext == "csv":
        df = pd.read_csv(file_path, dtype=str, keep_default_na=False, nrows=100)
    else:
        df = pd.read_excel(file_path, dtype=str, keep_default_na=False, nrows=100)
    headers = [str(c).strip() for c in df.columns]
    sample_rows = [dict(row) for _, row in df.iterrows()]
    return headers, sample_rows


def mapping_report_from_file(
    db: Session,
    content: bytes,
    file_name: str,
    provider_template: str | None = None,
) -> dict:
    file_path = save_upload_file(content, file_name)
    headers, _sample = _load_headers_from_file(file_path, file_name)
    report = generate_mapping_report(db, headers, provider_template=provider_template)
    report["file_name"] = file_name
    return report


def mapping_validate_from_file(
    db: Session,
    content: bytes,
    file_name: str,
    provider_template: str | None = None,
) -> dict:
    file_path = save_upload_file(content, file_name)
    headers, sample_rows = _load_headers_from_file(file_path, file_name)
    validation = validate_mapping(db, headers, sample_rows, provider_template=provider_template)
    report = generate_mapping_report(db, headers, provider_template=provider_template)
    return {
        "file_name": file_name,
        "validation": validation,
        "mapping_report": report["mapping_report"],
        "detected_headers": report["detected_headers"],
    }


def mapping_standardize_payload(rows: list[dict], column_map: dict[str, str | None]) -> dict:
    standardized = standardize_mapped_rows(rows, column_map)
    previews: dict[str, list] = {}
    for field in {v for v in column_map.values() if v}:
        previews[field] = standardize_preview(rows, field)
    return {"standardized_rows": standardized, "previews": previews}
