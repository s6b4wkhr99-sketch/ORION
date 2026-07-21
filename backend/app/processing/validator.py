"""Layer 02 — Data validation (Volume 09 Section 21)."""

import re

from app.mapping.data_dictionary import RECOMMENDED_UPLOAD_FIELDS, REQUIRED_UPLOAD_FIELDS, resolve_column

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
    "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT",
    "VA", "WA", "WV", "WI", "WY", "DC",
}


def is_valid_email(email: str | None) -> bool:
    if not email:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip(), re.I))


def normalize_zip(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if "-" in text:
        text = text.split("-", 1)[0].strip()
    digits = "".join(c for c in text if c.isdigit())
    if len(digits) >= 5:
        return digits[:5]
    return digits or None


def normalize_state(state: str | None) -> str | None:
    if not state:
        return None
    code = state.strip().upper()
    return code if code in US_STATES else code[:2] if len(code) == 2 else None


def validate_state(state: str | None) -> bool:
    if not state:
        return False
    return normalize_state(state) in US_STATES


def validate_revenue(value: float | None) -> bool:
    if value is None:
        return True
    return value >= 0


def validate_conversion_rate(value: float | None) -> bool:
    if value is None:
        return True
    return 0 <= value <= 100


def validate_column_map(column_map: dict[str, str | None]) -> dict:
    missing_required = [c for c in REQUIRED_UPLOAD_FIELDS if not resolve_column(column_map, c)]
    missing_recommended = [c for c in RECOMMENDED_UPLOAD_FIELDS if not resolve_column(column_map, c)]
    is_valid = len(missing_required) == 0
    return {
        "is_valid": is_valid,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "mapped_columns": {k: v for k, v in column_map.items() if v},
    }


def row_quality_flags(customer: dict) -> dict[str, bool]:
    email = customer.get("email_address") or customer.get("email")
    zip_val = customer.get("zip_code") or customer.get("zip")
    state = customer.get("state")
    return {
        "valid_email": is_valid_email(email),
        "has_zip": bool(zip_val),
        "has_state": validate_state(state),
    }
