"""RFC-001 — Auto Mapping Engine (Header Detection, Alias Lookup, Confidence)."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.mapping.data_dictionary import (
    ALL_FIELDS,
    DICTIONARY_VERSION,
    REQUIRED_UPLOAD_FIELDS,
    UPLOAD_SOURCE_MAPPINGS,
)
from app.mapping.rfc_constants import (
    CONFIDENCE_AI_MAX,
    CONFIDENCE_AI_MIN,
    CONFIDENCE_ALIAS_MAX,
    CONFIDENCE_ALIAS_MIN,
    CONFIDENCE_EXACT,
    CONFIDENCE_PROVIDER_MAX,
    CONFIDENCE_PROVIDER_MIN,
    CONFIDENCE_REVIEW_THRESHOLD,
    MATCH_AI_SIMILARITY,
    MATCH_ALIAS,
    MATCH_EXACT,
    MATCH_PROVIDER_TEMPLATE,
    MATCH_UNKNOWN,
    PROVIDER_UPLOAD_HEADERS,
    STATUS_IGNORED,
    STATUS_MAPPED,
    STATUS_REVIEW,
)
from app.mapping.standardization import standardize_row
from app.models.auto_mapping import FieldAlias, FieldMaster, ProviderUploadTemplate
from app.processing.validator import is_valid_email, normalize_zip, validate_state

_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")
_VENDOR_PREFIX_RE = re.compile(
    r"^(?:datalogix|acxiom|experian|liveramp)\s*[-–—:]+\s*",
    re.IGNORECASE,
)


def normalize_header(header: str) -> str:
    return _NORMALIZE_RE.sub("", header.strip().lower())


def strip_vendor_prefix(header: str) -> str:
    """Remove vendor prefixes such as 'Datalogix - ' before alias lookup."""
    text = header.strip()
    stripped = _VENDOR_PREFIX_RE.sub("", text).strip()
    return stripped or text


def header_lookup_keys(header: str) -> list[str]:
    """Normalized header keys to try — full label first, then vendor-stripped label."""
    keys: list[str] = []
    for text in (header, strip_vendor_prefix(header)):
        norm = normalize_header(text)
        if norm and norm not in keys:
            keys.append(norm)
    return keys


@dataclass
class MappingRow:
    uploaded_header: str
    internal_field: str | None
    match_type: str
    confidence: float
    status: str
    suggestion: str | None = None

    def to_dict(self) -> dict:
        return {
            "uploaded_header": self.uploaded_header,
            "internal_field": self.internal_field,
            "match_type": self.match_type,
            "confidence": round(self.confidence, 1),
            "status": self.status,
            "suggestion": self.suggestion,
        }


def detect_headers(columns: list[str]) -> list[str]:
    return [str(c).strip() for c in columns if str(c).strip()]


def _build_alias_index(db: Session, version: str = DICTIONARY_VERSION) -> dict[str, tuple[str, float, str]]:
    index: dict[str, tuple[str, float, str]] = {}
    for alias in db.query(FieldAlias).filter(FieldAlias.version == version, FieldAlias.approved.is_(True)).all():
        key = normalize_header(alias.alias_header)
        index[key] = (alias.internal_field, alias.confidence, alias.match_type or MATCH_ALIAS)
    for source, target, _dtype, _required in UPLOAD_SOURCE_MAPPINGS:
        key = normalize_header(source)
        if key not in index:
            index[key] = (target, float(CONFIDENCE_ALIAS_MAX), MATCH_ALIAS)
    return index


_CANONICAL_EXACT: dict[str, str] = {
    "email": "email_address",
    "state": "state",
    "zip": "zip_code",
    "firstname": "first_name",
    "lastname": "last_name",
    "phone": "phone",
    "city": "city",
    "gender": "gender",
}


def _build_exact_index() -> dict[str, str]:
    index = {normalize_header(f.name): f.name for f in ALL_FIELDS}
    index.update(_CANONICAL_EXACT)
    return index


def _build_provider_index(db: Session, template_name: str | None, version: str = DICTIONARY_VERSION) -> dict[str, str]:
    index: dict[str, str] = {}
    query = db.query(ProviderUploadTemplate).filter(ProviderUploadTemplate.version == version)
    if template_name:
        query = query.filter(ProviderUploadTemplate.template_name == template_name)
    for row in query.all():
        index[normalize_header(row.source_header)] = row.internal_field
    if template_name and template_name in PROVIDER_UPLOAD_HEADERS:
        for source, target in PROVIDER_UPLOAD_HEADERS[template_name]:
            index.setdefault(normalize_header(source), target)
    return index


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, normalize_header(a), normalize_header(b)).ratio()


def _resolve_unknown(header: str, candidates: list[str]) -> tuple[str | None, float]:
    if not candidates:
        return None, 0.0
    best_field: str | None = None
    best_score = 0.0
    for candidate in candidates:
        score = _similarity(header, candidate)
        if score > best_score:
            best_score = score
            best_field = candidate
    return best_field, best_score * 100


def auto_map_headers(
    db: Session,
    headers: list[str],
    provider_template: str | None = None,
) -> list[MappingRow]:
    exact_index = _build_exact_index()
    alias_index = _build_alias_index(db)
    provider_index = _build_provider_index(db, provider_template)
    candidate_fields = sorted({f.name for f in ALL_FIELDS})

    rows: list[MappingRow] = []
    for header in headers:
        lookup_keys = header_lookup_keys(header)
        if not lookup_keys:
            continue

        matched = False
        for key_index, norm in enumerate(lookup_keys):
            if norm in exact_index:
                rows.append(MappingRow(
                    uploaded_header=header,
                    internal_field=exact_index[norm],
                    match_type=MATCH_EXACT,
                    confidence=CONFIDENCE_EXACT,
                    status=STATUS_MAPPED,
                ))
                matched = True
                break

            if norm in alias_index:
                internal, conf, mtype = alias_index[norm]
                rows.append(MappingRow(
                    uploaded_header=header,
                    internal_field=internal,
                    match_type=mtype if mtype in {MATCH_ALIAS, MATCH_EXACT} else MATCH_ALIAS,
                    confidence=float(CONFIDENCE_ALIAS_MAX if key_index else (conf or CONFIDENCE_ALIAS_MIN + 3)),
                    status=STATUS_MAPPED,
                ))
                matched = True
                break

            if norm in provider_index:
                rows.append(MappingRow(
                    uploaded_header=header,
                    internal_field=provider_index[norm],
                    match_type=MATCH_PROVIDER_TEMPLATE,
                    confidence=float((CONFIDENCE_PROVIDER_MIN + CONFIDENCE_PROVIDER_MAX) / 2),
                    status=STATUS_MAPPED,
                ))
                matched = True
                break

        if matched:
            continue

        suggestion, score = _resolve_unknown(strip_vendor_prefix(header), candidate_fields)
        if score >= CONFIDENCE_REVIEW_THRESHOLD and suggestion:
            rows.append(MappingRow(
                uploaded_header=header,
                internal_field=suggestion,
                match_type=MATCH_AI_SIMILARITY,
                confidence=min(score, float(CONFIDENCE_AI_MAX)),
                status=STATUS_MAPPED if score >= CONFIDENCE_AI_MIN else STATUS_REVIEW,
                suggestion=suggestion,
            ))
            continue

        rows.append(MappingRow(
            uploaded_header=header,
            internal_field=None,
            match_type=MATCH_UNKNOWN,
            confidence=score,
            status=STATUS_REVIEW if score >= 40 else STATUS_IGNORED,
            suggestion=suggestion,
        ))

    return rows


def build_column_map_from_report(report: list[MappingRow]) -> dict[str, str | None]:
    column_map: dict[str, str | None] = {}
    for row in report:
        if row.internal_field and row.status in {STATUS_MAPPED, STATUS_REVIEW}:
            column_map[row.uploaded_header] = row.internal_field
        else:
            column_map[row.uploaded_header] = None
    return column_map


def generate_mapping_report(
    db: Session,
    headers: list[str],
    provider_template: str | None = None,
) -> dict:
    detected = detect_headers(headers)
    rows = auto_map_headers(db, detected, provider_template=provider_template)
    mapped_count = sum(1 for r in rows if r.internal_field and r.status == STATUS_MAPPED)
    review_count = sum(1 for r in rows if r.status == STATUS_REVIEW)
    unknown_count = sum(1 for r in rows if r.match_type == MATCH_UNKNOWN)

    return {
        "detected_headers": detected,
        "mapping_report": [r.to_dict() for r in rows],
        "summary": {
            "total_headers": len(detected),
            "mapped": mapped_count,
            "review": review_count,
            "unknown": unknown_count,
            "auto_mapped": mapped_count + review_count,
        },
        "column_map": build_column_map_from_report(rows),
        "unknown_fields": [r.uploaded_header for r in rows if r.match_type == MATCH_UNKNOWN],
        "unmapped_columns": [r.uploaded_header for r in rows if not r.internal_field],
    }


def validate_mapping(
    db: Session,
    headers: list[str],
    sample_rows: list[dict] | None = None,
    provider_template: str | None = None,
) -> dict:
    report = generate_mapping_report(db, headers, provider_template=provider_template)
    column_map = report["column_map"]

    duplicate_headers = [h for h in headers if headers.count(h) > 1]
    missing_required = [
        field for field in REQUIRED_UPLOAD_FIELDS
        if field not in column_map.values()
    ]

    email_col = next((k for k, v in column_map.items() if v == "email_address"), None)
    zip_col = next((k for k, v in column_map.items() if v == "zip_code"), None)
    state_col = next((k for k, v in column_map.items() if v == "state"), None)

    email_errors = 0
    zip_errors = 0
    state_errors = 0
    for row in sample_rows or []:
        if email_col and row.get(email_col) and not is_valid_email(str(row.get(email_col))):
            email_errors += 1
        if zip_col and row.get(zip_col) and not normalize_zip(str(row.get(zip_col))):
            zip_errors += 1
        if state_col and row.get(state_col) and not validate_state(str(row.get(state_col))):
            state_errors += 1

    is_valid = len(missing_required) == 0 and len(duplicate_headers) == 0
    return {
        "is_valid": is_valid,
        "missing_required": missing_required,
        "duplicate_columns": list(dict.fromkeys(duplicate_headers)),
        "email_format_errors": email_errors,
        "zip_format_errors": zip_errors,
        "state_format_errors": state_errors,
        "mapped_columns": {k: v for k, v in column_map.items() if v},
        "mapping_summary": report["summary"],
    }


def standardize_mapped_rows(rows: list[dict], column_map: dict[str, str | None]) -> list[dict]:
    standardized: list[dict] = []
    for row in rows:
        internal_row: dict[str, str | None] = {}
        for source_col, internal_field in column_map.items():
            if not internal_field:
                continue
            internal_row[internal_field] = row.get(source_col)
        standardized.append(standardize_row(internal_row))
    return standardized
