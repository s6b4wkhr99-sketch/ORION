"""
Chronic / back-pain geographic reference signals for Pain Index enrichment.

Sources (2025–2026 public studies):
- Novaalab Chronic Pain Map — top U.S. cities by recurring pain index (0–100)
  https://novaalab.com/blogs/infos/chronic-pain-map
- Felician University — back-health city rankings (provider access, walkability)
  https://absn.felician.edu/best-cities-achy-back/
- April ABA — U.S. back-pain prevalence, cost, occupational burden statistics
  https://www.aprilaba.com/resources/57-back-pain-statistics
"""

from __future__ import annotations

import re

CHRONIC_PAIN_GEO_VERSION = "2026.07-chronic-pain-v1"

# Novaalab top recurring-pain metros (pain index ≈ 94–99 / 100).
CHRONIC_PAIN_TIER1_CITIES: frozenset[tuple[str, str]] = frozenset(
    {
        ("NV", "LAS VEGAS"),
        ("FL", "ORLANDO"),
        ("FL", "TAMPA"),
        ("OH", "CLEVELAND"),
        ("AZ", "PHOENIX"),
    }
)

# Additional high-burden metros cited in Novaalab + occupational pain literature.
CHRONIC_PAIN_TIER2_CITIES: frozenset[tuple[str, str]] = frozenset(
    {
        ("FL", "JACKSONVILLE"),
        ("FL", "MIAMI"),
        ("TN", "MEMPHIS"),
        ("GA", "AUGUSTA"),
        ("NC", "WINSTON SALEM"),
        ("TX", "EL PASO"),
        ("PA", "PHILADELPHIA"),
        ("MI", "DETROIT"),
        ("IN", "INDIANAPOLIS"),
        ("MO", "ST LOUIS"),
        ("KY", "LOUISVILLE"),
    }
)

# Felician lowest-ranked back-care cities → compounded therapeutic need / access friction.
BACK_CARE_BURDEN_TIER1_CITIES: frozenset[tuple[str, str]] = frozenset(
    {
        ("FL", "LAKELAND"),
        ("NC", "WINSTON SALEM"),
        ("GA", "AUGUSTA"),
        ("TN", "MEMPHIS"),
        ("TX", "EL PASO"),
    }
)

# Felician highest-ranked back-care cities → slightly lower geo pain amplification.
BACK_CARE_FRIENDLY_CITIES: frozenset[tuple[str, str]] = frozenset(
    {
        ("WI", "MADISON"),
        ("TX", "AUSTIN"),
        ("FL", "SARASOTA"),
        ("WI", "MILWAUKEE"),
        ("IA", "DES MOINES"),
        ("UT", "SALT LAKE CITY"),
        ("NE", "OMAHA"),
        ("DC", "WASHINGTON"),
    }
)

# State-level chronic pain index (0–100) blended from:
# - Novaalab state representation (NV, FL, OH, AZ highest)
# - April ABA occupational / SES burden (construction, service, lower-income prevalence)
# - Felician back-care burden inverse (WI, IA, UT lower; TN, GA, FL pockets higher)
STATE_CHRONIC_PAIN_INDEX: dict[str, float] = {
    "NV": 99.0,
    "FL": 96.0,
    "OH": 94.0,
    "AZ": 93.0,
    "TN": 88.0,
    "GA": 85.0,
    "NC": 83.0,
    "PA": 78.0,
    "MI": 76.0,
    "IN": 74.0,
    "MO": 73.0,
    "KY": 72.0,
    "AL": 71.0,
    "LA": 70.0,
    "SC": 70.0,
    "WV": 69.0,
    "MS": 69.0,
    "AR": 68.0,
    "TX": 67.0,
    "OK": 66.0,
    "CA": 64.0,
    "NY": 63.0,
    "IL": 62.0,
    "NJ": 61.0,
    "MD": 60.0,
    "VA": 59.0,
    "MA": 58.0,
    "CT": 57.0,
    "RI": 56.0,
    "NM": 55.0,
    "CO": 52.0,
    "OR": 51.0,
    "WA": 50.0,
    "MN": 48.0,
    "UT": 47.0,
    "NE": 46.0,
    "IA": 45.0,
    "WI": 44.0,
    "VT": 43.0,
    "NH": 43.0,
    "ME": 42.0,
    "ID": 41.0,
    "MT": 40.0,
    "WY": 39.0,
    "ND": 38.0,
    "SD": 38.0,
    "AK": 37.0,
    "HI": 36.0,
    "DE": 55.0,
    "DC": 58.0,
}

# National anchors from April ABA statistics (used for tier labeling / tooltips).
US_CHRONIC_LBP_PREVALENCE_PCT = 28.0
US_ANNUAL_BACK_PAIN_HEALTHCARE_COST_B = 86.0
US_BACK_PAIN_HEALTHCARE_COST_PER_PATIENT = 1440.0
US_LOST_WORKDAYS_MILLIONS = 186.7


def _normalize_city(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9 ]", "", (value or "").upper()).strip()


def _normalize_state(value: str | None) -> str:
    return (value or "").strip().upper()[:2]


def state_chronic_pain_score(state: str | None) -> float:
    """Return 0–100 chronic/back-pain geography score for a U.S. state."""
    code = _normalize_state(state)
    if not code:
        return 55.0
    return STATE_CHRONIC_PAIN_INDEX.get(code, 55.0)


def state_chronic_pain_tier(state: str | None) -> str:
    score = state_chronic_pain_score(state)
    if score >= 90:
        return "Very High Chronic Pain Geography"
    if score >= 75:
        return "High Chronic Pain Geography"
    if score >= 60:
        return "Moderate Chronic Pain Geography"
    if score >= 45:
        return "Lower Chronic Pain Geography"
    return "Low Chronic Pain Geography"


def chronic_pain_city_boost(
    *,
    state: str | None,
    city: str | None,
) -> dict[str, float | str | bool]:
    """
    City/state chronic pain modifier for customer-level Pain Index (Rule-059 geo layer).

    Tier-1 Novaalab pain capitals: +0.22
    Tier-2 high-burden metros: +0.14
    Back-care burden cities (Felician bottom-5): +0.10 additive
    Back-care friendly cities: -0.06 moderation
    """
    state_code = _normalize_state(state)
    city_key = _normalize_city(city)
    boost = 0.0
    reasons: list[str] = []

    if (state_code, city_key) in CHRONIC_PAIN_TIER1_CITIES:
        boost = 0.22
        reasons.append("novaalab_top5_chronic_pain_city")
    elif (state_code, city_key) in CHRONIC_PAIN_TIER2_CITIES:
        boost = 0.14
        reasons.append("chronic_pain_tier2_metro")

    if (state_code, city_key) in BACK_CARE_BURDEN_TIER1_CITIES:
        boost += 0.10
        reasons.append("felician_low_back_care_access")

    if (state_code, city_key) in BACK_CARE_FRIENDLY_CITIES:
        boost -= 0.06
        reasons.append("felician_high_back_care_access")

    state_score = state_chronic_pain_score(state_code)
    if boost < 0.14 and state_score >= 88:
        boost = max(boost, 0.12)
        reasons.append("state_chronic_pain_corridor")

    boost = round(max(-0.06, min(0.32, boost)), 4)
    tier = "tier1_chronic_pain" if boost >= 0.20 else "tier2_chronic_pain" if boost >= 0.12 else "none"

    return {
        "chronic_pain_geo_boost": boost,
        "chronic_pain_state_score": state_score,
        "chronic_pain_tier": tier,
        "chronic_pain_match": boost >= 0.12,
        "chronic_pain_geo_reasons": ",".join(reasons) if reasons else "none",
        "chronic_pain_geo_version": CHRONIC_PAIN_GEO_VERSION,
    }
