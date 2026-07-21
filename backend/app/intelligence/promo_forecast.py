"""Baseline conversion vs standing-promo uplift layers."""

from __future__ import annotations

from app.campaign.standing_promo_demand import (
    STANDING_PROMO_CONVERSION_BIAS,
    standing_promo_outreach_product,
)
from app.commercial.promotion_policy import promotion_pct
from app.intelligence.promotion_policy_constants import (
    PROMO_CONVERSION_ELASTICITY,
    PROMO_FORECAST_UPLIFT_ENABLED,
    PROMO_MAX_UPLIFTED_MULTIPLIER,
    PROMO_SKU_CONVERSION_FLOOR,
)

_DEFAULT_PRODUCT = "Master S4"


def promo_outreach_sku(
    *,
    intelligence_product: str | None,
    purchase_power_category: str | None,
    ceragem_segment: str | None,
) -> str | None:
    return standing_promo_outreach_product(
        intelligence_product,
        purchase_power=purchase_power_category,
        ceragem_segment=ceragem_segment,
    )


def promo_uplift_multiplier(
    *,
    outreach_product: str | None,
    purchase_power_index: float,
    promotion_pct: float,
) -> float:
    """Standing-promo conversion expansion beyond baseline intelligence rate."""
    if not PROMO_FORECAST_UPLIFT_ENABLED:
        return 1.0

    product = outreach_product or ""
    floor = float(PROMO_SKU_CONVERSION_FLOOR.get(product, STANDING_PROMO_CONVERSION_BIAS.get(product, 1.0)))
    bias = max(floor, float(STANDING_PROMO_CONVERSION_BIAS.get(product, 1.0)))

    pp_factor = 1.0
    if purchase_power_index < 0.45 and promotion_pct >= 0.18:
        pp_factor = 1.0 + promotion_pct * 0.35
    elif promotion_pct >= 0.15:
        pp_factor = 1.0 + promotion_pct * 0.18
    elif promotion_pct >= 0.10:
        pp_factor = 1.0 + promotion_pct * 0.10

    elasticity = 1.0 + promotion_pct * PROMO_CONVERSION_ELASTICITY if promotion_pct > 0 else 1.0
    return round(bias * pp_factor * elasticity, 6)


def promotion_pct_for_product(product: str | None) -> float:
    return promotion_pct(product or "")


def apply_promo_layers(
    *,
    baseline_conversion: float,
    intelligence_product: str | None,
    purchase_power_category: str | None,
    ceragem_segment: str | None,
    purchase_power_index: float,
    product_price: float,
    target_customers: int = 1,
) -> dict:
    outreach = promo_outreach_sku(
        intelligence_product=intelligence_product,
        purchase_power_category=purchase_power_category,
        ceragem_segment=ceragem_segment,
    )
    promo_pct = promotion_pct_for_product(outreach or intelligence_product)
    promo_mult = promo_uplift_multiplier(
        outreach_product=outreach,
        purchase_power_index=purchase_power_index,
        promotion_pct=promo_pct,
    )
    uplifted_conversion = round(
        min(baseline_conversion * promo_mult, baseline_conversion * PROMO_MAX_UPLIFTED_MULTIPLIER),
        6,
    )
    promo_uplift = round(max(0.0, uplifted_conversion - baseline_conversion), 6)
    baseline_orders = round(target_customers * baseline_conversion, 6)
    uplifted_orders = round(target_customers * uplifted_conversion, 6)
    return {
        "promo_outreach_product": outreach,
        "promotion_pct": promo_pct,
        "promo_uplift_multiplier": promo_mult,
        "baseline_conversion": baseline_conversion,
        "promo_uplift": promo_uplift,
        "conversion_rate": uplifted_conversion,
        "baseline_orders": baseline_orders,
        "expected_orders": uplifted_orders,
        "baseline_revenue": round(baseline_orders * product_price, 4),
        "expected_revenue": round(uplifted_orders * product_price, 4),
    }
