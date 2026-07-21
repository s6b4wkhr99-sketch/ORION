"""Volume 15 Section 16 — Metric normalization."""

import re
from typing import Any

import pandas as pd

from app.providers.config import METRIC_ALIASES


def normalize_header(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _safe_int(value) -> int:
    if value is None or str(value).strip() == "":
        return 0
    try:
        return int(float(str(value).replace(",", "")))
    except ValueError:
        return 0


def _safe_float(value) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        text = str(value).replace(",", "").replace("%", "").replace("$", "")
        return float(text)
    except ValueError:
        return None


def _safe_str(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def build_metric_column_map(headers: list[str], extra_aliases: dict[str, list[str]] | None = None) -> dict[str, str | None]:
    normalized = {normalize_header(h): h for h in headers}
    aliases = dict(METRIC_ALIASES)
    if extra_aliases:
        for key, values in extra_aliases.items():
            aliases.setdefault(key, []).extend(values)

    mapping: dict[str, str | None] = {}
    for internal, alias_list in aliases.items():
        mapping[internal] = None
        for alias in alias_list:
            if alias in normalized:
                mapping[internal] = normalized[alias]
                break
    return mapping


def normalize_row_metrics(row: pd.Series, column_map: dict[str, str | None]) -> dict[str, Any]:
    """Map provider row to internal metric fields only."""
    result: dict[str, Any] = {}
    for internal, source_col in column_map.items():
        if not source_col:
            continue
        raw = row.get(source_col)
        if internal in {"actual_revenue"}:
            result[internal] = _safe_float(raw)
        elif internal in {
            "actual_orders",
            "total_sent",
            "delivered",
            "opened",
            "unique_open",
            "clicked",
            "unique_click",
            "bounce",
            "unsubscribe",
        }:
            result[internal] = _safe_int(raw)
        else:
            result[internal] = _safe_str(raw)
    return result
