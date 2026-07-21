"""Revenue Forecast Engine — Section 19 (Rules 068–070)."""

from app.reference.registry import (
    LE_FRAME_COMMISSION_RATE,
    LE_FRAME_INCENTIVE_BY_SKU,
    PRODUCT_FORECAST_PRICES,
    PRODUCT_GROSS_SALES,
)
from app.intelligence.promo_forecast import apply_promo_layers

CONSERVATIVE_RATES = {
    "High": 0.0075,
    "Mid-High": 0.0050,
    "Mid": 0.0035,
    "Mid-Low": 0.0025,
    "Low": 0.00075,
}

LE_FRAME_INCENTIVE_RATE = LE_FRAME_COMMISSION_RATE
DEFAULT_TARGET_CUSTOMERS = 1
_DEFAULT_PRODUCT = "Master S4"


def tier_from_ceragem_segment(segment: str) -> str:
    from app.intelligence.ceragem_rules import parse_ceragem_tier

    tier = parse_ceragem_tier(segment)
    if tier == "High+":
        return "High"
    if tier == "Mid-High+":
        return "Mid-High"
    if tier == "Mid+":
        return "Mid"
    if tier == "Mid-Low+":
        return "Mid-Low"
    return "Low"


def rule_068_expected_orders(*, target_customers: int, conversion_rate: float) -> dict:
    """Rule-068: Expected Orders = Target Customers × Conservative Conversion Rate."""
    orders = round(target_customers * conversion_rate, 6)
    return {
        "target_customers": target_customers,
        "conservative_conversion_rate": conversion_rate,
        "expected_orders": orders,
    }


def rule_069_expected_revenue(*, expected_orders: float, product_price: float) -> dict:
    """Rule-069: Expected Revenue = Expected Orders × Gross Sales Price."""
    revenue = round(expected_orders * product_price, 4)
    return {"expected_orders": expected_orders, "product_price": product_price, "expected_revenue": revenue}


def rule_070_le_frame_incentive(*, expected_orders: float, product: str) -> dict:
    """Rule-070: Le Frame Incentive = Expected Orders × SKU commission (15% of gross sales)."""
    unit = LE_FRAME_INCENTIVE_BY_SKU.get(product, LE_FRAME_INCENTIVE_BY_SKU[_DEFAULT_PRODUCT])
    incentive = round(expected_orders * unit, 4)
    gross_price = PRODUCT_GROSS_SALES.get(product, PRODUCT_GROSS_SALES[_DEFAULT_PRODUCT])
    gross_revenue = round(expected_orders * gross_price, 4)
    return {
        "expected_orders": expected_orders,
        "product": product,
        "le_frame_incentive": incentive,
        "le_frame_unit": unit,
        "rate": LE_FRAME_COMMISSION_RATE,
        "gross_revenue": gross_revenue,
    }


def forecast_customer(
    *,
    ceragem_segment: str,
    recommended_product: str,
    target_customers: int = 1,
    pain_index: float = 0.0,
    purchase_power_index: float = 0.0,
    purchase_power_category: str | None = None,
    email_response_index: float = 0.0,
    brand_familiarity_index: float = 0.0,
    purchase_potential_score: float = 0.0,
    pain_geo_boost: float = 0.0,
) -> dict:
    """Per-customer revenue forecast with geographic and intelligence multipliers."""
    tier = tier_from_ceragem_segment(ceragem_segment)
    rate = CONSERVATIVE_RATES.get(tier, CONSERVATIVE_RATES["Low"])

    intelligence_multiplier = 1.0
    intelligence_multiplier += pain_index * 0.12 + pain_geo_boost * 0.10
    intelligence_multiplier += purchase_power_index * 0.14 + purchase_potential_score * 0.10
    intelligence_multiplier += email_response_index * 0.10 + brand_familiarity_index * 0.08
    baseline_rate = round(min(rate * intelligence_multiplier, rate * 2.2), 6)

    price = PRODUCT_FORECAST_PRICES.get(recommended_product, PRODUCT_FORECAST_PRICES[_DEFAULT_PRODUCT])
    promo_layers = apply_promo_layers(
        baseline_conversion=baseline_rate,
        intelligence_product=recommended_product,
        purchase_power_category=purchase_power_category,
        ceragem_segment=ceragem_segment,
        purchase_power_index=purchase_power_index,
        product_price=price,
        target_customers=target_customers,
    )

    orders_result = rule_068_expected_orders(
        target_customers=target_customers,
        conversion_rate=promo_layers["conversion_rate"],
    )
    revenue_result = rule_069_expected_revenue(
        expected_orders=orders_result["expected_orders"],
        product_price=price,
    )
    incentive_result = rule_070_le_frame_incentive(
        expected_orders=orders_result["expected_orders"],
        product=recommended_product,
    )

    return {
        "tier": tier,
        "baseline_conversion": promo_layers["baseline_conversion"],
        "promo_uplift": promo_layers["promo_uplift"],
        "promo_outreach_product": promo_layers["promo_outreach_product"],
        "promo_uplift_multiplier": promo_layers["promo_uplift_multiplier"],
        "conversion_rate": promo_layers["conversion_rate"],
        "baseline_orders": promo_layers["baseline_orders"],
        "expected_orders": orders_result["expected_orders"],
        "baseline_revenue": promo_layers["baseline_revenue"],
        "expected_revenue": revenue_result["expected_revenue"],
        "le_frame_incentive": incentive_result["le_frame_incentive"],
    }


def run_forecast_engine(ctx) -> None:
    """Section 19.5 workflow — runs after Recommendation Engine."""
    from app.intelligence.types import IntelligenceContext

    assert isinstance(ctx, IntelligenceContext)
    product = ctx.recommended_product or _DEFAULT_PRODUCT
    segment = ctx.ceragem_segment or "Mid-Low + Wellness"

    result = forecast_customer(
        ceragem_segment=segment,
        recommended_product=product,
        target_customers=DEFAULT_TARGET_CUSTOMERS,
        pain_index=float(ctx.pain_index or 0),
        purchase_power_index=float(ctx.purchase_power_index or 0),
        purchase_power_category=ctx.purchase_power_category,
        email_response_index=float(ctx.email_response_index or 0),
        brand_familiarity_index=float(ctx.brand_familiarity_index or 0),
        purchase_potential_score=float((ctx.zip_intelligence or {}).get("purchase_potential_score") or 0),
        pain_geo_boost=float((ctx.zip_intelligence or {}).get("pain_geo_boost") or 0),
    )

    ctx.add_trace(
        "Rule-068", "Expected Orders Rule",
        {"target_customers": DEFAULT_TARGET_CUSTOMERS, "tier": result["tier"]},
        rule_068_expected_orders(
            target_customers=DEFAULT_TARGET_CUSTOMERS,
            conversion_rate=result["conversion_rate"],
        ),
        "Expected Orders = Target × Conservative Conversion Rate.",
    )
    ctx.add_trace(
        "Rule-069", "Expected Revenue Rule",
        {"recommended_product": product},
        rule_069_expected_revenue(
            expected_orders=result["expected_orders"],
            product_price=PRODUCT_FORECAST_PRICES.get(product, PRODUCT_FORECAST_PRICES[_DEFAULT_PRODUCT]),
        ),
        "Expected Revenue = Expected Orders × Gross Sales Price.",
    )
    ctx.add_trace(
        "Rule-070", "Le Frame Incentive Rule",
        {"recommended_product": product, "expected_orders": result["expected_orders"]},
        rule_070_le_frame_incentive(
            expected_orders=result["expected_orders"],
            product=product,
        ),
        "Le Frame Incentive = Expected Orders × SKU commission (15% of gross sales).",
    )

    ctx.baseline_conversion = result["baseline_conversion"]
    ctx.promo_uplift = result["promo_uplift"]
    ctx.baseline_revenue = result["baseline_revenue"]
    ctx.expected_conversion = result["conversion_rate"]
    ctx.expected_revenue = result["expected_revenue"]
    ctx.expected_orders = result["expected_orders"]
    ctx.le_frame_incentive = result["le_frame_incentive"]

    ctx.add_trace(
        "Rule-RF", "Revenue Forecast Engine",
        {"ceragem_segment": segment, "recommended_product": product},
        {
            "baseline_conversion": ctx.baseline_conversion,
            "promo_uplift": ctx.promo_uplift,
            "baseline_revenue": ctx.baseline_revenue,
            "expected_conversion": ctx.expected_conversion,
            "expected_orders": ctx.expected_orders,
            "expected_revenue": ctx.expected_revenue,
            "le_frame_incentive": ctx.le_frame_incentive,
            "promo_outreach_product": result.get("promo_outreach_product"),
            "promo_uplift_multiplier": result.get("promo_uplift_multiplier"),
        },
        "Baseline intelligence forecast + standing-promo uplift layer.",
    )


# Backward-compatible helpers
def forecast(*, ceragem_segment: str, recommended_product: str) -> tuple[float, float]:
    result = forecast_customer(ceragem_segment=ceragem_segment, recommended_product=recommended_product)
    return result["conversion_rate"], result["expected_revenue"]


def le_frame_incentive(expected_revenue: float) -> float:
    """Aggregate helper — 15% of gross expected revenue."""
    return round(expected_revenue * LE_FRAME_COMMISSION_RATE, 4)


def le_frame_incentive_for_product(product: str, expected_orders: float = 1.0) -> float:
    unit = LE_FRAME_INCENTIVE_BY_SKU.get(product, LE_FRAME_INCENTIVE_BY_SKU[_DEFAULT_PRODUCT])
    return round(expected_orders * unit, 4)
