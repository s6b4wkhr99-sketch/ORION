"""GAP-calibration adjustments for Rule-065 (buyer-profile backlog v1).

Applied after ladder pick + geo caps; does not alter standing promo KPI paths.
"""

from __future__ import annotations

from app.intelligence.ceragem_rules import segment_axis_is_pain

GAP_CALIBRATION_VERSION = "2026.07-gap-v1"

_VALUE_PRIZM = frozenset(
    {
        "Simple Life",
        "Caregiving Households",
        "Unknown",
        "Kids and Cul-de-Sacs",
        "Aging in Place",
        "Wellness Seekers",
    },
)


def _step_down_ladder(product: str, ladder: list[str], *, steps: int = 1) -> str:
    if product not in ladder:
        return product
    idx = ladder.index(product)
    return ladder[min(idx + steps, len(ladder) - 1)]


def apply_gap_calibration_adjustments(
    product: str,
    inputs,
    ladder: list[str],
) -> tuple[str, str | None]:
    """Return (product, adjustment_reason|None)."""
    from app.intelligence.product_ladders import (
        STANDARD_VALUE_S_SKU,
        is_high_end_purchase_zip,
        is_lower_income_context,
        normalize_prizm_key,
    )

    prizm_key = normalize_prizm_key(inputs.prizm_segment)
    pain_axis = segment_axis_is_pain(inputs.ceragem_segment) or inputs.pain_index_category in {
        "High",
        "Medium",
    }
    wellness = not pain_axis
    lower_income = is_lower_income_context(
        zip_income_tier=inputs.zip_income_tier,
        purchase_power_category=inputs.purchase_power_category,
        premium_zip=inputs.premium_zip,
    )
    high_end = is_high_end_purchase_zip(
        premium_zip=inputs.premium_zip,
        zip_income_tier=inputs.zip_income_tier,
        purchase_power_category=inputs.purchase_power_category,
    )

    # V9 cap — flagship only on true high-end ZIP + High PP (GAP: buyer V9 ~2% vs prospect ~22%).
    if product == "Master V9":
        if not high_end:
            stepped = _step_down_ladder(product, ladder)
            if stepped != product:
                return stepped, "gap_v9_cap_not_high_end"
        elif inputs.purchase_power_category != "High":
            stepped = _step_down_ladder(product, ladder)
            if stepped != product:
                return stepped, "gap_v9_cap_pp_not_high"

    # M4 gate — reduce Pause M4 on wellness profiles without lower-income context (GAP: M4 over-recommend).
    if product == "Pause M4" and wellness and not lower_income:
        if prizm_key in _VALUE_PRIZM or inputs.purchase_power_category in {"Low", "Medium"}:
            if STANDARD_VALUE_S_SKU in ladder:
                return STANDARD_VALUE_S_SKU, "gap_m4_gate_to_s4"
            stepped = _step_down_ladder(product, ladder)
            if stepped != product and stepped != "Pause M4":
                return stepped, "gap_m4_gate_ladder_down"

    # S4 default — value wellness cohorts anchor to Master S4 before M-line (buyer V4/S4 heavy).
    if wellness and product in {"Pause M6", "Pause M6s", "Pause M4"}:
        if prizm_key in _VALUE_PRIZM and inputs.purchase_power_category in {"Low", "Medium"}:
            if STANDARD_VALUE_S_SKU in ladder:
                return STANDARD_VALUE_S_SKU, "gap_s4_default_value_wellness"

    return product, None
