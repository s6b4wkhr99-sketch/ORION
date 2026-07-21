"""Volume 06 Section 22 — Deterministic campaign forecast calculations."""

from app.intelligence.forecasting import (
    CONSERVATIVE_RATES,
    LE_FRAME_INCENTIVE_RATE,
    le_frame_incentive,
    rule_068_expected_orders,
    rule_069_expected_revenue,
    tier_from_ceragem_segment,
)
from app.reference.registry import PRODUCT_FORECAST_PRICES

RULE_VERSION = "Volume 06 — Rules 068–070"
FORECAST_VERSION = "Volume 06 v1.0"

# Historical email performance baseline (conservative planning)
DEFAULT_HISTORICAL_CTR = 0.025
CAMPAIGN_TYPE_MULTIPLIER = {
    "Email": 1.0,
    "Direct Mail": 0.85,
    "SMS": 0.92,
    "Multi-Channel": 1.1,
}


def forecast_accuracy(actual_revenue: float, expected_revenue: float) -> float | None:
    """RULE-FOR-004 / Rule-068 follow-on: Actual Revenue ÷ Expected Revenue."""
    if expected_revenue <= 0:
        return None
    return round(actual_revenue / expected_revenue, 4)


def compute_campaign_forecast(
    *,
    target_customers: int,
    ceragem_distribution: dict[str, int] | None = None,
    product_distribution: dict[str, int] | None = None,
    campaign_type: str = "Email",
    historical_ctr: float | None = None,
    campaign_cost: float | None = None,
) -> dict:
    """
    Deterministic campaign forecast — Section 22.3 calculation sequence.
    Reproducible for identical inputs.
    """
    ceragem_distribution = ceragem_distribution or {"Mid-Low + Wellness": target_customers}
    product_distribution = product_distribution or {"Master S4": target_customers}

    total_weight = sum(ceragem_distribution.values()) or 1
    expected_orders = 0.0
    expected_revenue = 0.0

    for segment, count in ceragem_distribution.items():
        if count <= 0:
            continue
        tier = tier_from_ceragem_segment(segment)
        base_rate = CONSERVATIVE_RATES.get(tier, CONSERVATIVE_RATES["Low"])
        type_mult = CAMPAIGN_TYPE_MULTIPLIER.get(campaign_type, 1.0)
        hist = historical_ctr or DEFAULT_HISTORICAL_CTR
        conversion_rate = round(base_rate * type_mult * (1 + hist), 6)

        orders_part = rule_068_expected_orders(target_customers=count, conversion_rate=conversion_rate)
        expected_orders += orders_part["expected_orders"]

        segment_products = product_distribution or {"Master S4": count}
        prod_total = sum(segment_products.values()) or 1
        for product, pcount in segment_products.items():
            share = pcount / prod_total
            segment_orders = orders_part["expected_orders"] * share
            price = PRODUCT_FORECAST_PRICES.get(product, PRODUCT_FORECAST_PRICES["Master S4"])
            rev_part = rule_069_expected_revenue(expected_orders=segment_orders, product_price=price)
            expected_revenue += rev_part["expected_revenue"]

    expected_orders = round(expected_orders, 4)
    expected_revenue = round(expected_revenue, 2)
    incentive = le_frame_incentive(expected_revenue)
    cost = campaign_cost or round(expected_revenue * 0.12, 2)
    expected_roi = round(expected_revenue / cost, 4) if cost else None
    expected_cpc = round(cost / max(target_customers * (historical_ctr or DEFAULT_HISTORICAL_CTR), 1), 4)
    expected_cpa = round(cost / max(expected_orders, 0.01), 4)
    aov = round(expected_revenue / max(expected_orders, 0.01), 2)
    confidence = round(min(0.95, 0.55 + (target_customers / 10000) * 0.2), 4)

    return {
        "forecast_version": FORECAST_VERSION,
        "rule_version": RULE_VERSION,
        "expected_customers": target_customers,
        "expected_orders": expected_orders,
        "expected_revenue": expected_revenue,
        "expected_conversion": round(expected_orders / max(target_customers, 1), 6),
        "expected_roi": expected_roi,
        "expected_cpc": expected_cpc,
        "expected_cpa": expected_cpa,
        "expected_average_order_value": aov,
        "forecast_confidence": confidence,
        "le_frame_incentive": incentive,
        "campaign_cost": cost,
    }
