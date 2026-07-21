"""ORION Commercial Intelligence Engine — Version 2026.07."""

from __future__ import annotations

from app.commercial.catalog import active_products, get_runtime_version
from app.commercial.promotion_policy import is_promotion_active, promo_code, promotion_pct
from app.reference.registry import (
    LE_FRAME_COMMISSION_RATE,
    PRODUCT_CATALOG,
    PRODUCT_GROSS_SALES,
    PRODUCT_MAX_PROMOTION,
)

# Estimated Ceragem unit cost for net-profit planning (corporate placeholder).
CERAGEM_UNIT_COST_RATIO = 0.55

PRICE_RESISTANCE_DOWNGRADE: dict[str, str] = {
    "Master V9": "Master V7",
    "Pause M10": "Master V7",
    "Master V7": "Master V6",
    "Master V6": "Master V5",
    # Keep FDA Class 2 V-line — do not downgrade therapeutic SKUs into Pause M massage line.
    "Master V5": "Master S4",
    "Master S4": "Pause M4",
    "Pause M6": "Pause M4",
    # Downgrade toward a cheaper accessible SKU (Pause M6s $4,799 → Pause M4 $3,999), not upward.
    "Pause M6s": "Pause M4",
    "Pause M4": "Master S4",
}

HIGH_RESISTANCE_THRESHOLD = 0.65
MODERATE_RESISTANCE_THRESHOLD = 0.45

# Standing-promo FDA Class 2 SKUs — preserve in Mid-Low mass segments unless extreme resistance.
FDA_STANDING_PROMO_SKUS: frozenset[str] = frozenset({"Master V5", "Master V6"})


def _product_lookup() -> dict[str, dict]:
    lookup = {p["code"]: p for p in active_products()}
    for product in PRODUCT_CATALOG:
        if not product.get("active", True):
            continue
        code = product["code"]
        if code not in lookup:
            lookup[code] = product
    return lookup


def calculate_price_resistance_score(ctx) -> float:
    """
    Price Resistance Intelligence (0 = low resistance, 1 = high resistance).
    Higher resistance steers recommendations toward lower-priced SKUs.
    """
    zip_intel = ctx.zip_intelligence or {}
    intermediate = ctx.datalogix_intermediate or {}

    income_numeric = intermediate.get("estimated_income_numeric")
    if income_numeric is None:
        income_numeric = zip_intel.get("median_income")

    if income_numeric is not None and float(income_numeric) > 0:
        income_resistance = 1.0 - min(1.0, float(income_numeric) / 150_000)
    else:
        income_resistance = 0.55

    pp_resistance = 1.0 - float(ctx.purchase_power_index or 0)
    lifestyle_resistance = 1.0 - float(ctx.lifestyle_index or 0)
    zip_affluence_resistance = 1.0 - float(zip_intel.get("median_income_context") or 0)
    digital_resistance = 1.0 - float(ctx.email_response_index or 0)
    brand_resistance = 1.0 - float(ctx.brand_familiarity_index or 0)
    pain_relief = float(ctx.pain_index or 0)
    pain_resistance = max(0.0, 0.35 - pain_relief * 0.2)

    prizm = (ctx.prizm_proxy_segment or "").strip()
    if prizm in {"Established Elite", "Suburban Sophisticates", "Booming with Confidence"}:
        segment_resistance = 0.1
    elif prizm == "Simple Life":
        segment_resistance = 0.75
    else:
        segment_resistance = 0.45

    score = (
        income_resistance * 0.22
        + pp_resistance * 0.18
        + lifestyle_resistance * 0.12
        + zip_affluence_resistance * 0.12
        + digital_resistance * 0.08
        + brand_resistance * 0.08
        + pain_resistance * 0.08
        + segment_resistance * 0.12
    )
    return round(min(1.0, max(0.0, score)), 4)


def default_promotion_amount(product_code: str) -> float:
    """MSRP-to-gross discount already embedded in catalog gross_sales."""
    product = _product_lookup().get(product_code)
    if not product:
        return 0.0
    msrp = float(product.get("msrp") or 0)
    gross_sales = float(product.get("gross_sales") or product.get("selling_price") or 0)
    return round(max(0.0, msrp - gross_sales), 2)


def effective_customer_payment(product_code: str) -> float:
    """Customer-facing price after active promo discount; otherwise catalog gross."""
    from app.reference.registry import normalize_product_code

    product_code = normalize_product_code(product_code)
    gross = float(PRODUCT_GROSS_SALES.get(product_code) or 0)
    if gross <= 0:
        product = _product_lookup().get(product_code, {})
        gross = float(product.get("gross_sales") or product.get("selling_price") or product.get("msrp") or 0)
    pct = promotion_pct(product_code)
    if pct > 0:
        return round(gross * (1.0 - pct), 2)
    return round(gross, 2)


def _catalog_promotion_amount(product: dict) -> float:
    msrp = float(product.get("msrp") or 0)
    gross_sales = float(product.get("gross_sales") or product.get("selling_price") or 0)
    return round(max(0.0, msrp - gross_sales), 2)


def build_commercial_kpis(product_code: str, promotion_amount: float | None = None) -> dict:
    """Commercial KPI Guide — matches Ceragem NP% sheet (Gross Sales − Commission − COGS)."""
    product = _product_lookup().get(product_code, {})
    msrp = float(product.get("msrp") or 0)
    gross_sales = float(product.get("gross_sales") or product.get("selling_price") or msrp)
    selling_price = float(product.get("selling_price") or gross_sales)
    catalog_promo = _catalog_promotion_amount(product)
    recommended_promotion = round(float(promotion_amount if promotion_amount is not None else catalog_promo), 2)

    active_code = promo_code(product_code) if is_promotion_active(product_code) else None
    promotion_pct_value = promotion_pct(product_code) if active_code else round(catalog_promo / msrp, 4) if msrp > 0 else 0.0
    if active_code and msrp > 0 and promotion_pct_value <= 0:
        promotion_pct_value = round(catalog_promo / msrp, 4)

    commission = round(gross_sales * LE_FRAME_COMMISSION_RATE, 2)
    ceragem_cost = float(product.get("ceragem_cogs") or round(gross_sales * CERAGEM_UNIT_COST_RATIO, 2))
    total_cogs = round(ceragem_cost, 2)
    net_profit = round(gross_sales - commission - ceragem_cost, 2)
    margin_base = gross_sales - commission
    net_profit_pct = round(net_profit / margin_base, 4) if margin_base > 0 else 0.0

    return {
        "commercial_version": get_runtime_version(),
        "msrp": msrp,
        "selling_price": selling_price,
        "gross_sales": gross_sales,
        "max_promotion": float(product.get("max_promotion") or 0),
        "recommended_promotion": recommended_promotion,
        "promotion_pct": promotion_pct_value,
        "promo_code": active_code,
        "retail_additional_contribution": 0.0,
        "le_frame_incentive_unit": commission,
        "le_frame_incentive_rate": LE_FRAME_COMMISSION_RATE,
        "customer_payment": gross_sales,
        "ceragem_cost": ceragem_cost,
        "total_cogs": total_cogs,
        "net_profit": net_profit,
        "net_profit_pct": net_profit_pct,
    }


def cap_promotion(product_code: str, proposed_promotion: float) -> dict:
    """Maximum Promotion Guide — never exceed approved discount."""
    product = _product_lookup().get(product_code, {})
    max_allowed = float(product.get("max_promotion") or PRODUCT_MAX_PROMOTION.get(product_code, 0))
    capped = min(max(0.0, proposed_promotion), max_allowed)
    return {
        "product": product_code,
        "proposed_promotion": round(proposed_promotion, 2),
        "max_promotion": max_allowed,
        "recommended_promotion": round(capped, 2),
        "capped": proposed_promotion > max_allowed,
    }


def adjust_product_for_price_resistance(
    product_code: str,
    price_resistance: float,
    *,
    ceragem_segment: str | None = None,
    pain_index_category: str | None = None,
    preserve_value_floor: bool = False,
) -> dict:
    """Commercial precedence — downgrade SKU when price resistance is elevated."""
    original = product_code
    adjusted = product_code
    reason = "no_adjustment"

    # Preserve FDA V5/V6 only for pain-dominant BD profiles — not all Mid-Low standing promos.
    preserve_fda_promo = (
        product_code in FDA_STANDING_PROMO_SKUS
        and pain_index_category == "High"
        and ceragem_segment
        and "Pain" in ceragem_segment
        and price_resistance < HIGH_RESISTANCE_THRESHOLD
    )
    if preserve_fda_promo:
        return {
            "original_product": original,
            "adjusted_product": adjusted,
            "price_resistance_score": price_resistance,
            "adjustment_reason": "fda_standing_promo_preserved",
            "adjusted": False,
        }

    # Pause S4 / M6s are already the accessible price floor for value cohorts — keep them unless
    # resistance is extreme, in which case step down to the cheapest SKU (Pause M4).
    if preserve_value_floor and product_code in {"Master S4", "Pause M6s"}:
        if price_resistance >= HIGH_RESISTANCE_THRESHOLD:
            return {
                "original_product": original,
                "adjusted_product": "Pause M4",
                "price_resistance_score": price_resistance,
                "adjustment_reason": "value_floor_high_resistance_to_m4",
                "adjusted": "Pause M4" != original,
            }
        return {
            "original_product": original,
            "adjusted_product": product_code,
            "price_resistance_score": price_resistance,
            "adjustment_reason": "value_floor_preserved",
            "adjusted": False,
        }

    if price_resistance >= HIGH_RESISTANCE_THRESHOLD:
        for _ in range(2):
            adjusted = PRICE_RESISTANCE_DOWNGRADE.get(adjusted, adjusted)
        reason = "high_price_resistance_double_downgrade"
    elif price_resistance >= MODERATE_RESISTANCE_THRESHOLD:
        adjusted = PRICE_RESISTANCE_DOWNGRADE.get(adjusted, adjusted)
        reason = "moderate_price_resistance_downgrade"

    return {
        "original_product": original,
        "adjusted_product": adjusted,
        "price_resistance_score": price_resistance,
        "adjustment_reason": reason,
        "adjusted": adjusted != original,
    }


def apply_zip_income_proxy(ctx) -> None:
    """Infer household income from ZIP median when Datalogix estimated income is missing."""
    intermediate = dict(ctx.datalogix_intermediate or {})
    has_income = intermediate.get("estimated_income_numeric") is not None
    has_categorical = bool(intermediate.get("estimated_income_categorical"))
    if has_income or has_categorical:
        return

    median = (ctx.zip_intelligence or {}).get("median_income")
    if median is None or float(median) <= 0:
        return

    intermediate["estimated_income_numeric"] = float(median)
    intermediate["estimated_income_source"] = "zip_median_baseline"
    intermediate["estimated_income_reference"] = "unitedstateszipcodes.org/ACS-B19013"
    ctx.datalogix_intermediate = intermediate


def run_commercial_pre_engine(ctx) -> None:
    """Commercial Intelligence precedes recommendation — price resistance score."""
    score = calculate_price_resistance_score(ctx)
    ctx.price_resistance_score = score
    ctx.commercial_version = get_runtime_version()

    ctx.add_trace(
        "Rule-CI-PR",
        "Price Resistance Intelligence",
        {
            "purchase_power_index": ctx.purchase_power_index,
            "lifestyle_index": ctx.lifestyle_index,
            "zip_median_income": (ctx.zip_intelligence or {}).get("median_income"),
        },
        {"price_resistance_score": score},
        "Price resistance influences SKU and promotion recommendations.",
    )


def run_commercial_post_engine(ctx) -> None:
    """Apply promotion caps and commercial KPIs after SKU recommendation."""
    product = ctx.recommended_product
    if not product:
        return

    proposed = default_promotion_amount(product)
    capped = cap_promotion(product, proposed)
    kpis = build_commercial_kpis(product, capped["recommended_promotion"])

    ctx.recommended_promotion = capped["recommended_promotion"]
    ctx.promo_code = kpis.get("promo_code")
    ctx.commercial_kpis = kpis
    ctx.commercial_version = get_runtime_version()

    ctx.add_trace(
        "Rule-CI-MP",
        "Maximum Promotion Guide",
        {"product": product, "proposed_promotion": proposed},
        capped,
        "Promotion never exceeds Ceragem maximum allowable discount.",
    )
    ctx.add_trace(
        "Rule-CI-KPI",
        "Commercial KPI Guide",
        {"product": product},
        kpis,
        "Commercial KPIs attached to recommendation for Mission Control.",
    )


def run_commercial_intelligence_engine(ctx) -> None:
    """Full commercial pass: pre (price resistance) is called before recommendation; post after."""
    run_commercial_pre_engine(ctx)
