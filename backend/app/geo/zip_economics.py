"""
ZIP economic baseline — aligned with unitedstateszipcodes.org median household income rankings.

Source methodology:
- U.S. Census ACS 5-year Table B19013 (Median Household Income)
- https://www.unitedstateszipcodes.org/rankings/median_household_income/
- National reference median and $250,001 top-code match Census suppression on affluent ZIPs.
"""

from __future__ import annotations

# ACS 2023 5-year national median (unitedstateszipcodes.org site reference).
NATIONAL_MEDIAN_HOUSEHOLD_INCOME = 77_719
CENSUS_TOP_CODE_INCOME = 250_001
PREMIUM_INCOME_THRESHOLD = 100_000
AFFLUENT_INCOME_THRESHOLD = 150_000
MID_INCOME_LOWER_BOUND = 60_000

INCOME_SOURCE_LABEL = "unitedstateszipcodes.org/ACS-B19013"


def normalize_median_income(value: float | int | None) -> float | None:
    if value is None:
        return None
    try:
        income = float(value)
    except (TypeError, ValueError):
        return None
    if income <= 0:
        return None
    return income


def income_tier(median_income: float | None, *, premium_zip: bool = False) -> str:
    """
    ZIP affluence tier used for economic power and purchase-potential logic.

    High  — premium ZIP or >= $100K (or Census top-code)
    Mid   — $60K–$99K
    Lower — < $60K
    """
    income = normalize_median_income(median_income)
    if premium_zip:
        return "High"
    if income is None:
        return "Unknown"
    if income >= CENSUS_TOP_CODE_INCOME or income >= PREMIUM_INCOME_THRESHOLD:
        return "High"
    if income >= MID_INCOME_LOWER_BOUND:
        return "Mid"
    return "Lower"


def economic_power_score(median_income: float | None, *, premium_zip: bool = False) -> float:
    """0–1 geographic economic strength from ZIP median income."""
    income = normalize_median_income(median_income)
    if income is None:
        return 0.0
    if premium_zip or income >= CENSUS_TOP_CODE_INCOME:
        return 1.0
    return round(min(1.0, income / AFFLUENT_INCOME_THRESHOLD), 4)


def purchase_potential_score(
    median_income: float | None,
    *,
    premium_zip: bool = False,
    tier: str | None = None,
) -> float:
    """
    ZIP-level purchase potential for Ceragem SKU selection.
    Weighted toward unitedstateszipcodes.org affluent ZIP research baseline.
    """
    resolved_tier = tier or income_tier(median_income, premium_zip=premium_zip)
    tier_base = {"High": 0.85, "Mid": 0.55, "Lower": 0.25, "Unknown": 0.35}
    base = tier_base.get(resolved_tier, 0.35)
    economic = economic_power_score(median_income, premium_zip=premium_zip)
    return round(min(1.0, base * 0.55 + economic * 0.45), 4)


def income_context(median_income: float | None) -> float:
    """Normalized median income context (Rule-021 supporting signal)."""
    income = normalize_median_income(median_income)
    if income is None:
        return 0.0
    return round(min(1.0, income / AFFLUENT_INCOME_THRESHOLD), 4)


def build_zip_economics(
    median_income: float | None,
    *,
    premium_zip: bool = False,
    income_vintage: str = "ACS-5yr",
) -> dict:
    tier = income_tier(median_income, premium_zip=premium_zip)
    return {
        "income_source": INCOME_SOURCE_LABEL,
        "income_vintage": income_vintage,
        "national_median_reference": NATIONAL_MEDIAN_HOUSEHOLD_INCOME,
        "income_tier": tier,
        "economic_power_score": economic_power_score(median_income, premium_zip=premium_zip),
        "purchase_potential_score": purchase_potential_score(median_income, premium_zip=premium_zip, tier=tier),
        "median_income_context": income_context(median_income),
    }
