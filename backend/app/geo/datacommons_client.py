"""Data Commons REST API client — ZIP median income fallback (ACS B19013 equivalent)."""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import httpx

logger = logging.getLogger("cios.geo.datacommons")

API_BASE = "https://api.datacommons.org/v2"
MEDIAN_INCOME_VARIABLE = "Median_Income_Household"
PREFERRED_FACET_IMPORT = "CensusACS5YearSurvey"
ZIP_PATTERN = re.compile(r"^\d{5}$")
DEFAULT_BATCH_SIZE = 50
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_INTER_BATCH_SLEEP_SECONDS = 0.2


def _normalize_zip(value: str | None) -> str | None:
    if not value:
        return None
    digits = "".join(c for c in str(value).strip() if c.isdigit())
    if len(digits) >= 5:
        zip_code = digits[:5]
        return zip_code if ZIP_PATTERN.fullmatch(zip_code) else None
    return None


def _parse_income(value: Any) -> float | None:
    if value is None:
        return None
    try:
        income = float(value)
    except (TypeError, ValueError):
        return None
    if income <= 0:
        return None
    return income


def _pick_observation(
    entity_payload: dict[str, Any],
    facets: dict[str, Any] | None,
) -> tuple[float | None, str | None]:
    """Prefer ACS 5-year B19013-compatible facet; fall back to any available observation."""
    ordered = entity_payload.get("orderedFacets") or []
    if not ordered:
        return None, None

    preferred: list[dict[str, Any]] = []
    fallback: list[dict[str, Any]] = []
    for facet in ordered:
        facet_id = str(facet.get("facetId") or "")
        facet_meta = (facets or {}).get(facet_id) or {}
        if facet_meta.get("importName") == PREFERRED_FACET_IMPORT:
            preferred.append(facet)
        else:
            fallback.append(facet)

    for facet in preferred + fallback:
        observations = facet.get("observations") or []
        if not observations:
            continue
        latest = max(observations, key=lambda item: str(item.get("date") or ""))
        income = _parse_income(latest.get("value"))
        if income is not None:
            facet_id = str(facet.get("facetId") or "")
            facet_meta = (facets or {}).get(facet_id) or {}
            source = facet_meta.get("importName") or facet_id or "unknown"
            return income, str(source)
    return None, None


def _parse_observation_response(payload: dict[str, Any]) -> dict[str, float]:
    results: dict[str, float] = {}
    facets = payload.get("facets") or {}
    by_variable = (payload.get("byVariable") or {}).get(MEDIAN_INCOME_VARIABLE) or {}
    by_entity = by_variable.get("byEntity") or {}

    for entity_dcid, entity_payload in by_entity.items():
        if not str(entity_dcid).startswith("zip/"):
            continue
        zip_code = str(entity_dcid)[4:]
        if not ZIP_PATTERN.fullmatch(zip_code):
            continue
        income, _source = _pick_observation(entity_payload, facets)
        if income is not None:
            results[zip_code] = income
    return results


def fetch_zip_median_incomes(
    zips: set[str] | list[str],
    *,
    api_key: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    inter_batch_sleep_seconds: float = DEFAULT_INTER_BATCH_SLEEP_SECONDS,
) -> dict[str, float]:
    """
    Fetch median household income for ZIPs missing from local ACS bulk import.

    Uses Data Commons Observation API (Median_Income_Household, zip/{zip5} DCIDs).
    """
    if not api_key:
        raise ValueError("Data Commons API key is required")

    normalized = sorted({_normalize_zip(zip_code) for zip_code in zips if _normalize_zip(zip_code)})
    if not normalized:
        return {}

    incomes: dict[str, float] = {}
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    with httpx.Client(timeout=timeout_seconds) as client:
        for start in range(0, len(normalized), batch_size):
            batch = normalized[start : start + batch_size]
            body = {
                "variable": {"dcids": [MEDIAN_INCOME_VARIABLE]},
                "entity": {"dcids": [f"zip/{zip_code}" for zip_code in batch]},
                "select": ["entity", "variable", "value", "date", "facet"],
            }
            response = client.post(f"{API_BASE}/observation", headers=headers, json=body)
            response.raise_for_status()
            incomes.update(_parse_observation_response(response.json()))

            if start + batch_size < len(normalized) and inter_batch_sleep_seconds > 0:
                time.sleep(inter_batch_sleep_seconds)

    logger.info(
        "Data Commons ZIP income lookup: requested=%s resolved=%s",
        len(normalized),
        len(incomes),
    )
    return incomes
