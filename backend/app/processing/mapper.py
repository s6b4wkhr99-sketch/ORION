"""Layer 2 — RFC-001 Auto Mapping Engine column map (internal_field → source header)."""

import re
from typing import Any

from sqlalchemy.orm import Session

from app.mapping.auto_engine import generate_mapping_report
from app.mapping.data_dictionary import (
    DICTIONARY_VERSION,
    RECOMMENDED_UPLOAD_FIELDS,
    REQUIRED_UPLOAD_FIELDS,
    db_column,
    detect_duplicate_source_mappings,
    resolve_column,
)
from app.models.mapping import FieldMapping


def normalize_header(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def load_field_mappings(db: Session, version: str = DICTIONARY_VERSION) -> list[FieldMapping]:
    return db.query(FieldMapping).filter(FieldMapping.version == version).all()


def build_column_map(
    db: Session,
    headers: list[str],
    version: str = DICTIONARY_VERSION,
    provider_template: str | None = None,
) -> dict[str, str | None]:
    """Returns internal_field -> original header name."""
    report = generate_mapping_report(db, headers, provider_template=provider_template)
    column_map: dict[str, str | None] = {}

    for mapping in load_field_mappings(db, version):
        column_map.setdefault(mapping.target_field, None)

    for source_header, internal_field in report["column_map"].items():
        if not internal_field:
            continue
        column_map[internal_field] = source_header
        legacy = db_column(internal_field)
        if legacy != internal_field:
            column_map[legacy] = source_header

    return column_map


def validate_column_map(db: Session, column_map: dict[str, str | None], version: str = DICTIONARY_VERSION) -> dict:
    required_targets = {
        m.target_field
        for m in load_field_mappings(db, version)
        if m.required
    }
    missing_required = [t for t in required_targets if not resolve_column(column_map, t)]
    missing_recommended = [f for f in RECOMMENDED_UPLOAD_FIELDS if not resolve_column(column_map, f)]
    duplicate_sources = detect_duplicate_source_mappings(column_map)
    return {
        "is_valid": len(missing_required) == 0 and len(duplicate_sources) == 0,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "duplicate_sources": duplicate_sources,
        "mapped_columns": {k: v for k, v in column_map.items() if v},
    }


def extract_state_from_filename(filename: str) -> str | None:
    match = re.search(r"\b([A-Z]{2})\b", filename.upper())
    if match:
        return match.group(1)
    return None
