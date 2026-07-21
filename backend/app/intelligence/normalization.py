"""Normalization Engine — Rule-001, Rule-002, Rule-003, Rule-006."""

import re
from typing import Any

from app.intelligence.types import IntelligenceContext
from app.mapping.data_dictionary import resolve_column
from app.processing.validator import is_valid_email, normalize_state, normalize_zip

ZIP_PRIORITY_HEADERS = ["zip.1", "zip1", "zip", "zip code", "zipcode", "postal code", "postal"]


def normalize_header(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def apply_rule_001_zip(row: dict, headers: list[str], column_map: dict[str, str | None]) -> str | None:
    """Rule-001: If ZIP.1 exists use ZIP.1, otherwise use ZIP. Never merge."""
    normalized = {normalize_header(h): h for h in headers}
    for priority in ZIP_PRIORITY_HEADERS:
        if priority in normalized:
            val = row.get(normalized[priority])
            if val and str(val).strip():
                return normalize_zip(str(val))
    zip_col = resolve_column(column_map, "zip_code")
    if zip_col and row.get(zip_col):
        return normalize_zip(str(row.get(zip_col)))
    return None


def apply_rule_002_state(
    row: dict,
    column_map: dict[str, str | None],
    filename_state: str | None,
) -> str | None:
    """Rule-002: State column first, then upload filename."""
    state_col = column_map.get("state")
    if state_col and row.get(state_col):
        resolved = normalize_state(str(row.get(state_col)))
        if resolved:
            return resolved
    if filename_state:
        return normalize_state(filename_state)
    return None


def apply_rule_003_email(email: str | None) -> bool:
    """Rule-003: RFC-compliant email validation."""
    return is_valid_email(email)


def apply_rule_006_numeric(value: str | None) -> str | float | None:
    """Rule-006: Strip formatting from numeric values; preserve categorical codes."""
    if not value or not str(value).strip():
        return None
    text = str(value).strip()
    if text.upper() in {"X", "Y", "Z", "U"}:
        return text.upper()
    cleaned = text.replace(",", "").replace("$", "").replace("%", "").strip()
    try:
        num = float(cleaned)
        return int(num) if num == int(num) else num
    except ValueError:
        return text


def run_normalization_engine(
    ctx: IntelligenceContext,
    row: dict,
    headers: list[str],
    column_map: dict[str, str | None],
    filename_state: str | None,
) -> None:
    zip_val = apply_rule_001_zip(row, headers, column_map)
    ctx.customer["zip"] = zip_val
    ctx.add_trace(
        "Rule-001", "ZIP Priority Rule",
        {"headers": headers},
        {"zip": zip_val},
        "ZIP.1 takes priority over ZIP; one ZIP per customer.",
    )

    state_val = apply_rule_002_state(row, column_map, filename_state)
    ctx.customer["state"] = state_val
    ctx.add_trace(
        "Rule-002", "State Identification Rule",
        {"state_column": column_map.get("state"), "filename_state": filename_state},
        {"state": state_val},
        "State from column first, then filename.",
    )

    email = ctx.customer.get("email")
    ctx.email_valid = apply_rule_003_email(email)
    ctx.add_trace(
        "Rule-003", "Email Validation Rule",
        {"email": email},
        {"valid": ctx.email_valid},
        "Invalid emails stored but excluded from provider export.",
    )
