"""
Sleep-deprivation segmentation for Pause M Series affinity.

Combines Innerbody metro sleep-deprived cities with PRIZM / Ceragem / Datalogix
proxy signals aligned to CDC sleep-risk factors (age, income, stress, caregiving).

Source: https://www.innerbody.com/most-sleep-deprived-cities
"""

from __future__ import annotations

from app.intelligence.types import IntelligenceContext

SLEEP_SIGNAL_VERSION = "2026.07-sleep-segment-v1"

# PRIZM proxy segments correlated with CDC sleep-deprivation risk profile.
PRIZM_SLEEP_AFFINITY: dict[str, float] = {
    "Aging in Place": 0.20,
    "Caregiving Households": 0.16,
    "Simple Life": 0.18,
    "Kids and Cul-de-Sacs": 0.08,
}

# Ceragem segments where rest/sleep positioning fits better than therapeutic V.
CERAGEM_SLEEP_AFFINITY: dict[str, float] = {
    "Family Wellness": 0.12,
    "Mid-Low + Wellness": 0.10,
    "Mid-Low + Pain Index": 0.12,
}


def _collect_sleep_signals(ctx: IntelligenceContext) -> list[tuple[str, float]]:
    zip_intel = ctx.zip_intelligence or {}
    intermediate = ctx.datalogix_intermediate or {}
    prizm = ctx.prizm_proxy_segment or "Unknown"
    ceragem = ctx.ceragem_segment or ""
    pain = ctx.pain_index_category or "Low"
    lifestyle = ctx.lifestyle_category or "Low"
    purchase_power = ctx.purchase_power_category or "Low"
    zip_tier = str(zip_intel.get("income_tier") or "Unknown")

    city_boost = float(zip_intel.get("sleep_city_boost") or zip_intel.get("sleep_geo_boost") or 0.0)
    signals: list[tuple[str, float]] = []

    if city_boost >= 0.24:
        signals.append(("metro_tier1_sleep_deprived", 0.28))
    elif city_boost >= 0.14:
        signals.append(("metro_tier2_sleep_deprived", 0.16))

    prizm_weight = PRIZM_SLEEP_AFFINITY.get(prizm, 0.0)
    if prizm_weight:
        signals.append((f"prizm_{prizm.lower().replace(' ', '_')}", prizm_weight))

    if ceragem == "Family Wellness":
        signals.append(("ceragem_family_wellness", CERAGEM_SLEEP_AFFINITY["Family Wellness"]))
    elif ceragem == "Mid-Low + Wellness" and lifestyle == "Low":
        signals.append(("ceragem_midlow_wellness_rest", CERAGEM_SLEEP_AFFINITY["Mid-Low + Wellness"]))
    elif ceragem == "Mid-Low + Pain Index" and pain == "Medium" and lifestyle == "Low":
        signals.append(("ceragem_midlow_pain_rest", CERAGEM_SLEEP_AFFINITY["Mid-Low + Pain Index"]))

    if pain == "Medium" and lifestyle == "Low":
        signals.append(("pain_medium_rest_profile", 0.08))

    if purchase_power == "Low" and zip_tier in {"Lower", "Mid"} and prizm in {"Simple Life", "Unknown"}:
        signals.append(("economic_sleep_stress", 0.08))

    if "caregiving scenarios" in (intermediate.get("family_messaging_hints") or []):
        signals.append(("datalogix_caregiving_household", 0.10))

    household = (ctx.datalogix_signals or {}).get("household_composition") or ""
    if household in {"I", "J", "K"}:
        signals.append(("datalogix_mature_household_code", 0.06))

    return signals


def _resolve_sleep_segment(signals: list[tuple[str, float]], final_boost: float) -> str:
    if final_boost < 0.14:
        return "none"

    names = {name for name, _ in signals}
    if "metro_tier1_sleep_deprived" in names or "metro_tier2_sleep_deprived" in names:
        if any(n.startswith("prizm_") for n in names):
            return "metro_plus_prizm_sleep_affinity"
        return "metro_sleep_deprived"
    if any(n.startswith("prizm_simple_life") for n in names):
        return "simple_life_sleep_stress"
    if any("caregiving" in n for n in names):
        return "caregiver_fatigue"
    if "ceragem_midlow_pain_rest" in names or "pain_medium_rest_profile" in names:
        return "midlife_rest_gap"
    if "economic_sleep_stress" in names:
        return "economic_sleep_burden"
    if len(signals) >= 2:
        return "blended_sleep_affinity"
    if final_boost >= 0.18:
        return "prizm_sleep_affinity"
    return "sleep_affinity"


def compute_sleep_affinity(ctx: IntelligenceContext) -> dict[str, float | str | bool | list[str]]:
    zip_intel = ctx.zip_intelligence or {}
    city_boost = float(zip_intel.get("sleep_city_boost") or zip_intel.get("sleep_geo_boost") or 0.0)
    pain = ctx.pain_index_category or "Low"

    if pain == "High" and city_boost < 0.14:
        return {
            "sleep_signal_version": SLEEP_SIGNAL_VERSION,
            "sleep_city_boost": city_boost,
            "sleep_geo_boost": 0.0,
            "sleep_affinity_score": 0.0,
            "sleep_segment": "none",
            "sleep_deprivation_tier": "none",
            "sleep_deprivation_match": False,
            "sleep_signal_count": 0,
            "sleep_geo_reasons": "therapeutic_pain_preserved",
            "sleep_signal_names": [],
        }

    signals = _collect_sleep_signals(ctx)
    if not signals:
        return {
            "sleep_signal_version": SLEEP_SIGNAL_VERSION,
            "sleep_city_boost": city_boost,
            "sleep_geo_boost": 0.0,
            "sleep_affinity_score": 0.0,
            "sleep_segment": "none",
            "sleep_deprivation_tier": "none",
            "sleep_deprivation_match": False,
            "sleep_signal_count": 0,
            "sleep_geo_reasons": "none",
            "sleep_signal_names": [],
        }

    weights = sorted((weight for _, weight in signals), reverse=True)
    if weights[0] >= 0.24:
        final_boost = min(0.45, weights[0] + 0.12 * (len(weights) - 1))
    elif len(weights) >= 2:
        final_boost = min(0.40, weights[0] + weights[1] * 0.55)
    elif weights[0] >= 0.18:
        final_boost = weights[0]
    else:
        final_boost = 0.0

    final_boost = round(final_boost, 4)
    segment = _resolve_sleep_segment(signals, final_boost)
    signal_names = [name for name, _ in signals]

    tier = "none"
    if final_boost >= 0.24:
        tier = "high_sleep_affinity"
    elif final_boost >= 0.14:
        tier = "moderate_sleep_affinity"

    return {
        "sleep_signal_version": SLEEP_SIGNAL_VERSION,
        "sleep_city_boost": city_boost,
        "sleep_geo_boost": final_boost,
        "sleep_affinity_score": final_boost,
        "sleep_segment": segment,
        "sleep_deprivation_tier": tier,
        "sleep_deprivation_match": final_boost >= 0.14,
        "sleep_signal_count": len(signals),
        "sleep_geo_reasons": ",".join(signal_names) if signal_names else "none",
        "sleep_signal_names": signal_names,
    }


def apply_sleep_segment_intelligence(ctx: IntelligenceContext) -> None:
    """Merge geo + PRIZM + Ceragem + Datalogix sleep affinity before recommendation."""
    zip_intel = dict(ctx.zip_intelligence or {})
    if "sleep_city_boost" not in zip_intel:
        zip_intel["sleep_city_boost"] = float(zip_intel.get("sleep_geo_boost") or 0.0)

    signals = compute_sleep_affinity(ctx)
    ctx.zip_intelligence = {**zip_intel, **signals}

    ctx.add_trace(
        "Rule-SLP",
        "Sleep Deprivation Segmentation",
        {
            "prizm_proxy_segment": ctx.prizm_proxy_segment,
            "ceragem_segment": ctx.ceragem_segment,
            "pain_index_category": ctx.pain_index_category,
            "lifestyle_category": ctx.lifestyle_category,
            "purchase_power_category": ctx.purchase_power_category,
        },
        signals,
        "Pause M Series weight from metro sleep risk + PRIZM/Datalogix rest affinity.",
    )
