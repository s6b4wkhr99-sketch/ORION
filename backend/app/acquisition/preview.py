"""Upload preview — RFC-001 auto mapping report without persisting."""

import json

import pandas as pd
from sqlalchemy.orm import Session

from app.mapping.auto_engine import generate_mapping_report, validate_mapping
from app.mapping.data_dictionary import resolve_column
from app.processing.mapper import build_column_map, extract_state_from_filename, validate_column_map
from app.processing.duplicate import load_existing_email_keys, normalize_email_key
from app.processing.validator import is_valid_email, normalize_state, normalize_zip


def _load_dataframe(file_path: str, file_name: str) -> pd.DataFrame:
    ext = file_name.lower().split(".")[-1]
    if ext == "csv":
        return pd.read_csv(file_path, dtype=str, keep_default_na=False)
    return pd.read_excel(file_path, dtype=str, keep_default_na=False)


def _safe_str(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def preview_upload(db: Session, file_path: str, file_name: str) -> dict:
    df = _load_dataframe(file_path, file_name)
    headers = [str(c).strip() for c in df.columns]
    auto_report = generate_mapping_report(db, headers)
    column_map = build_column_map(db, headers)
    validation = validate_column_map(db, column_map)
    rfc_validation = validate_mapping(db, headers, [dict(row) for _, row in df.head(50).iterrows()])

    email_col = resolve_column(column_map, "email_address")
    zip_col = resolve_column(column_map, "zip_code")
    state_col = resolve_column(column_map, "state")
    state_hint = extract_state_from_filename(file_name)

    invalid_emails = 0
    missing_zip = 0
    missing_state = 0
    duplicate_emails = 0
    duplicate_emails_in_db = 0
    seen_emails: set[str] = set()
    existing_emails = load_existing_email_keys(db)

    for _, row in df.iterrows():
        email = _safe_str(row.get(email_col)) if email_col else None
        if email:
            key = normalize_email_key(email)
            if key:
                if key in seen_emails:
                    duplicate_emails += 1
                seen_emails.add(key)
                if key in existing_emails:
                    duplicate_emails_in_db += 1
            if not is_valid_email(email):
                invalid_emails += 1
        zip_val = _safe_str(row.get(zip_col)) if zip_col else None
        if not normalize_zip(zip_val):
            missing_zip += 1
        state_val = _safe_str(row.get(state_col)) if state_col else None
        if not normalize_state(state_val) and not state_hint:
            missing_state += 1

    mapping_report = auto_report["mapping_report"]
    unknown_fields = auto_report["unknown_fields"]

    mapping_preview = [
        {"uploaded_column": r["uploaded_header"], "internal_field": r["internal_field"]}
        for r in mapping_report
        if r.get("internal_field")
    ]
    unmapped = [
        {"uploaded_column": r["uploaded_header"], "internal_field": None}
        for r in mapping_report
        if not r.get("internal_field")
    ]

    return {
        "file_name": file_name,
        "total_rows": len(df),
        "headers": headers,
        "detected_headers": auto_report["detected_headers"],
        "validation": validation,
        "rfc_validation": rfc_validation,
        "fatal_errors": validation.get("missing_required", []),
        "warnings": validation.get("missing_recommended", []),
        "stats": {
            "duplicate_email": duplicate_emails,
            "duplicate_email_in_db": duplicate_emails_in_db,
            "invalid_email": invalid_emails,
            "missing_zip": missing_zip,
            "missing_state": missing_state,
            "unknown_fields": len(unknown_fields),
        },
        "unknown_fields": unknown_fields,
        "mapping_report": mapping_report,
        "mapping_summary": auto_report["summary"],
        "mapping_preview": mapping_preview,
        "unmapped_columns": unmapped,
        "column_map": validation.get("mapped_columns", {}),
    }
