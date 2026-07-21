"""RFC-001 — Data Standardization Engine."""

from __future__ import annotations

import re

from app.processing.validator import US_STATES, normalize_state, normalize_zip

US_STATE_NAMES: dict[str, str] = {
    "new jersey": "NJ",
    "new york": "NY",
    "connecticut": "CT",
    "california": "CA",
    "texas": "TX",
    "florida": "FL",
}

GENDER_MAP: dict[str, str] = {
    "m": "Male",
    "male": "Male",
    "f": "Female",
    "female": "Female",
}

BOOLEAN_YES = {"true", "yes", "y", "1"}
BOOLEAN_NO = {"false", "no", "n", "0"}


def standardize_state(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    upper = text.upper().replace(".", "")
    if upper in US_STATES:
        return upper
    named = US_STATE_NAMES.get(text.lower())
    if named:
        return named
    return normalize_state(text)


def standardize_zip(value: str | None) -> str | None:
    normalized = normalize_zip(value)
    if not normalized:
        return None
    if len(normalized) == 4:
        return normalized.zfill(5)
    return normalized


def standardize_gender(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    return GENDER_MAP.get(text.lower(), text.title())


def standardize_boolean(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text in BOOLEAN_YES:
        return "Yes"
    if text in BOOLEAN_NO:
        return "No"
    return str(value).strip()


def standardize_value(internal_field: str, value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    field = internal_field.lower()
    if field == "state":
        return standardize_state(text)
    if field in {"zip_code", "zip"}:
        return standardize_zip(text)
    if field == "gender":
        return standardize_gender(text)
    if field in {"online_access", "retail_card", "contact_permission", "permission"}:
        return standardize_boolean(text)
    if field == "email_address" or field == "email":
        return text.lower()
    return text


def standardize_row(row: dict[str, str | None]) -> dict[str, str | None]:
    return {key: standardize_value(key, val) for key, val in row.items()}


def standardize_preview(rows: list[dict], field: str, limit: int = 5) -> list[dict]:
    samples = []
    for row in rows[:limit]:
        raw = row.get(field)
        samples.append({
            "raw": raw,
            "standardized": standardize_value(field, raw),
        })
    return samples
