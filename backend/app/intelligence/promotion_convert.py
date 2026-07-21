"""Standing-promo up/down convert matrix — applied within active ladder rungs."""

from __future__ import annotations

from app.commercial.promotion_policy import is_promotion_active
from app.intelligence.ceragem_rules import segment_axis_is_pain
from app.intelligence.product_ladders import (
    is_lower_income_context,
    is_m10_eligible_zip,
    is_post_promo_v_accessible,
    normalize_prizm_key,
)
from app.intelligence.promotion_policy_constants import PROMO_CONVERT_MATRIX_ENABLED, PROMO_PRIMARY_SKU_ENABLED, V_VALUE_ENTRY_SKU

_VALUE_PRIZM = frozenset(
    {"Simple Life", "Caregiving Households", "Unknown", "Kids and Cul-de-Sacs", "Aging in Place", "Wellness Seekers"}
)


def _wellness(inputs) -> bool:
    return not segment_axis_is_pain(inputs.ceragem_segment) and inputs.pain_index_category != "High"


def _pain_axis(inputs) -> bool:
    return segment_axis_is_pain(inputs.ceragem_segment) or inputs.pain_index_category in {"High", "Medium"}


def _value_cohort(inputs) -> bool:
    prizm_key = normalize_prizm_key(inputs.prizm_segment)
    return prizm_key in _VALUE_PRIZM or inputs.purchase_power_category in {"Low", "Medium"}


def apply_promo_convert_matrix(product: str, inputs, ladder: list[str]) -> str:
    """Promo-window ladder moves — up-convert M6/M6s→M10, S4→V5/V6."""
    if not PROMO_CONVERT_MATRIX_ENABLED or not PROMO_PRIMARY_SKU_ENABLED:
        return product

    product = product.strip()
    wellness = _wellness(inputs)
    pain_axis = _pain_axis(inputs)
    lower_income = is_lower_income_context(
        zip_income_tier=inputs.zip_income_tier,
        purchase_power_category=inputs.purchase_power_category,
        premium_zip=inputs.premium_zip,
    )

    # M-line promo up-convert → Pause M10
    if (
        wellness
        and is_promotion_active("Pause M10")
        and is_m10_eligible_zip(
            premium_zip=inputs.premium_zip,
            zip_income_tier=inputs.zip_income_tier,
            purchase_power_category=inputs.purchase_power_category,
        )
        and product in {"Pause M4", "Pause M6", "Pause M6s"}
        and "Pause M10" in ladder
    ):
        return "Pause M10"

    # V-line promo up-convert from Master S4
    if pain_axis and product == V_VALUE_ENTRY_SKU:
        if is_promotion_active("Master V6"):
            v6_ok = is_post_promo_v_accessible(
                "Master V6",
                purchase_power_category=inputs.purchase_power_category,
                zip_income_tier=inputs.zip_income_tier,
            )
            if v6_ok and "Master V6" in ladder:
                return "Master V6"
        if is_promotion_active("Master V5"):
            v5_ok = is_post_promo_v_accessible(
                "Master V5",
                purchase_power_category=inputs.purchase_power_category,
                zip_income_tier=inputs.zip_income_tier,
            )
            if v5_ok and "Master V5" in ladder:
                return "Master V5"

    # M6s promo up from M4/M6 (wellness value cohort)
    if (
        wellness
        and lower_income
        and _value_cohort(inputs)
        and is_promotion_active("Pause M6s")
        and product in {"Pause M4", "Pause M6"}
        and "Pause M6s" in ladder
    ):
        if inputs.lifestyle_category in {"Medium", "High"} or inputs.purchase_power_category == "Medium":
            return "Pause M6s"

    # Master S4 SAVE30 wellness down from M4 when S4 promo active on value entry
    if (
        wellness
        and lower_income
        and is_promotion_active(V_VALUE_ENTRY_SKU)
        and product in {"Pause M4", "Pause M6", "Pause M6s"}
        and V_VALUE_ENTRY_SKU in ladder
        and inputs.lifestyle_category == "Low"
    ):
        return V_VALUE_ENTRY_SKU

    return product
