"""Layer 02 — Campaign report column mapping (Volume 09 Section 20)."""

import re
from typing import Any

from app.mapping.data_dictionary import CAMPAIGN_REPORT_ALIASES


def normalize_header(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def build_campaign_column_map(headers: list[str]) -> dict[str, str | None]:
    normalized = {normalize_header(h): h for h in headers}
    mapping: dict[str, str | None] = {}
    for field, aliases in CAMPAIGN_REPORT_ALIASES.items():
        mapping[field] = None
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized[alias]
                break
    return mapping


def validate_campaign_column_map(column_map: dict[str, str | None]) -> dict:
    has_metrics = any(column_map.get(f) for f in ("total_sent", "opened", "clicked"))
    has_identity = column_map.get("campaign_name") or column_map.get("campaign_id")
    is_valid = bool(has_identity and has_metrics)
    return {
        "is_valid": is_valid,
        "missing_required": [] if is_valid else ["campaign_name or campaign_id", "total_sent/opened/clicked metrics"],
        "mapped_columns": {k: v for k, v in column_map.items() if v},
    }
