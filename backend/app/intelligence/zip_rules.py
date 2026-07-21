"""ZIP Rule Library — Rules 018–024 (Volume 04 Section 11)."""

import re

from app.geo.zip_economics import build_zip_economics, income_context

ZIP_PATTERN = re.compile(r"^\d{5}(-\d{4})?$")


def rule_018_validate_zip(raw_zip: str | None, normalized_zip: str | None) -> dict:
    """Rule-018: Validate five-digit or ZIP+4 format; invalid ZIPs stored without intelligence."""
    raw = (raw_zip or "").strip()
    normalized = (normalized_zip or "").strip()

    if not raw and not normalized:
        return {"raw": raw_zip, "normalized": None, "valid": False, "reason": "missing"}

    if ZIP_PATTERN.match(raw):
        return {"raw": raw_zip, "normalized": normalized, "valid": True, "reason": "valid_format"}

    if normalized and len(normalized) == 5 and normalized.isdigit():
        return {"raw": raw_zip, "normalized": normalized, "valid": True, "reason": "normalized_valid"}

    return {"raw": raw_zip, "normalized": normalized or raw, "valid": False, "reason": "invalid_format"}


def rule_019_normalize_zip(value: str | None) -> str | None:
    """Rule-019: Strip ZIP+4 extension; intelligence always uses five-digit ZIP."""
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


def rule_020_lookup_zip(normalized_zip: str, reference: dict | None) -> dict:
    """Rule-020: Load reference row from zip_intelligence by normalized ZIP."""
    if not reference:
        return {
            "found": False,
            "zip": normalized_zip,
            "city": None,
            "state": None,
            "county": None,
            "median_income": None,
            "top_50_income_rank": False,
            "population": None,
        }
    return {
        "found": True,
        "zip": reference.get("zip", normalized_zip),
        "city": reference.get("city"),
        "state": reference.get("state"),
        "county": reference.get("county"),
        "median_income": reference.get("median_income"),
        "top_50_income_rank": bool(reference.get("top_50_income_rank")),
        "population": reference.get("population"),
    }


def rule_021_median_income(reference: dict) -> dict:
    """Rule-021: Median income baseline (unitedstateszipcodes.org / ACS B19013)."""
    median = reference.get("median_income")
    premium = bool(reference.get("top_50_income_rank"))
    economics = build_zip_economics(median, premium_zip=premium)
    return {
        "median_income": median,
        "median_income_context": economics["median_income_context"],
        "income_tier": economics["income_tier"],
        "economic_power_score": economics["economic_power_score"],
        "purchase_potential_score": economics["purchase_potential_score"],
        "income_source": economics["income_source"],
        "supporting_only": True,
    }


def rule_022_top50_income_zip(reference: dict) -> dict:
    """Rule-022: Top 50 Income ZIP premium geographic indicator."""
    is_premium = bool(reference.get("top_50_income_rank"))
    return {
        "premium_zip_indicator": is_premium,
        "top_50_income_rank": reference.get("top_50_income_rank", False),
        "supporting_only": True,
    }


def rule_023_state_verification(customer_state: str | None, reference_state: str | None) -> dict:
    """Rule-023: Log mismatch; never auto-correct customer state."""
    customer = (customer_state or "").strip().upper() or None
    reference = (reference_state or "").strip().upper() or None
    mismatch = bool(customer and reference and customer != reference)
    return {
        "customer_state": customer,
        "reference_state": reference,
        "mismatch": mismatch,
        "state_corrected": False,
        "exception": "state_zip_mismatch" if mismatch else None,
    }


def rule_024_reference_integrity() -> dict:
    """Rule-024: ZIP reference database is read-only during upload processing."""
    return {"reference_modified": False, "read_only": True}


def compose_zip_intelligence(
    *,
    validation: dict,
    lookup: dict,
    median: dict,
    top50: dict,
    state_check: dict,
) -> dict:
    """Section 11.5 — standardized ZIP intelligence outputs."""
    if not validation.get("valid") or not lookup.get("found"):
        return {
            "available": False,
            "normalized_zip": validation.get("normalized"),
            "geographic_purchasing_context": 0.0,
            "regional_economic_context": 0.0,
            "median_income_context": 0.0,
            "premium_zip_indicator": False,
            "state_intelligence": lookup.get("state"),
            "state_mismatch": state_check.get("mismatch", False),
            "reference": lookup,
        }

    economic = round(
        median.get("economic_power_score", median.get("median_income_context", 0.0)) * 0.7
        + (0.3 if top50.get("premium_zip_indicator") else 0.0),
        4,
    )
    geographic = round(
        economic * 0.6 + (0.4 if top50.get("premium_zip_indicator") else 0.1),
        4,
    )

    return {
        "available": True,
        "normalized_zip": validation.get("normalized"),
        "geographic_purchasing_context": geographic,
        "regional_economic_context": economic,
        "median_income_context": median.get("median_income_context", income_context(median.get("median_income"))),
        "median_income": median.get("median_income"),
        "premium_zip_indicator": top50.get("premium_zip_indicator", False),
        "income_tier": median.get("income_tier", "Unknown"),
        "economic_power_score": median.get("economic_power_score", 0.0),
        "purchase_potential_score": median.get("purchase_potential_score", 0.0),
        "income_source": median.get("income_source"),
        "state_intelligence": lookup.get("state"),
        "state_mismatch": state_check.get("mismatch", False),
        "city": lookup.get("city"),
        "county": lookup.get("county"),
        "population": lookup.get("population"),
        "reference": lookup,
    }
