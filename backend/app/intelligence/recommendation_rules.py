"""Recommendation Rule Library — Rules 065–067 (Volume 04 Section 18)."""

from dataclasses import dataclass

from app.reference.registry import (
    FDA_CLASS_2_PRODUCTS,
    PRIORITY_LEVELS as _PRIORITY_SEED,
    PRODUCT_PRICES,
)
from app.intelligence.ceragem_rules import parse_ceragem_tier, segment_axis_is_pain

CAMPAIGN_STRATEGIES = (
    "Premium Campaign",
    "Consultation Campaign",
    "Financing Campaign",
    "Educational Campaign",
    "Wellness Campaign",
)

PRIORITY_LEVELS = tuple(level[0] for level in _PRIORITY_SEED)
PRIORITY_TO_SCORE = {level[0]: level[2] for level in _PRIORITY_SEED}

_PAUSE_M_RANK = {"Pause M4": 1, "Pause M6": 2, "Pause M6s": 3, "Pause M10": 4}
_THERAPEUTIC_V_PRODUCTS = FDA_CLASS_2_PRODUCTS

# Accessible value SKUs — preserved from sleep/resistance stripping on wellness paths.
_VALUE_MASSAGE_PRODUCTS = {"Master S4", "Pause M6s", "Pause M4"}


@dataclass
class RecommendationInputs:
    ceragem_segment: str
    prizm_segment: str
    purchase_power_category: str
    pain_index_category: str
    lifestyle_category: str
    message_direction: str
    email_response_index: float
    premium_zip: bool
    customer_state: str | None = None
    zip_income_tier: str = "Unknown"
    zip_purchase_potential: float = 0.0
    price_resistance_score: float = 0.0
    sleep_geo_boost: float = 0.0
    sleep_deprivation_tier: str = "none"
    sleep_segment: str = "none"
    customer_id: str | None = None


def _preferred_pause_m_series(
    purchase_power: str,
    lifestyle: str,
    *,
    premium_zip: bool = False,
    zip_income_tier: str = "Unknown",
) -> str:
    from app.intelligence.product_ladders import is_m10_eligible_zip

    if is_m10_eligible_zip(
        premium_zip=premium_zip,
        zip_income_tier=zip_income_tier,
        purchase_power_category=purchase_power,
    ):
        return "Pause M10"
    if purchase_power == "High" or lifestyle == "High":
        return "Pause M6s"
    if purchase_power == "Medium" or lifestyle == "Medium":
        return "Pause M6s"
    return "Pause M4"


def _max_pause_m_series(current: str, target: str) -> str:
    if current not in _PAUSE_M_RANK:
        return target
    return current if _PAUSE_M_RANK[current] >= _PAUSE_M_RANK[target] else target


def _protect_value_massage(product: str, inputs: RecommendationInputs) -> bool:
    """Keep the accessible Pause S4 / M6s picks from being stripped for non-pain wellness buyers."""
    if product not in _VALUE_MASSAGE_PRODUCTS:
        return False
    if inputs.pain_index_category == "High":
        return False
    return not segment_axis_is_pain(inputs.ceragem_segment)


def _apply_standing_promo_primary(product: str, inputs: RecommendationInputs) -> str:
    """Prefer promo SKUs only when that promotion is currently active in the catalog."""
    return _apply_active_promo_primary(product, inputs)


def _apply_active_promo_primary(product: str, inputs: RecommendationInputs) -> str:
    """Promo-active expansion — value M/S nationwide; V5/V6 on pain profiles."""
    from app.commercial.promotion_policy import is_promotion_active
    from app.intelligence.product_ladders import (
        STANDARD_VALUE_M_SKU,
        STANDARD_VALUE_S_SKU,
        is_lower_income_context,
        is_m10_eligible_zip,
        is_post_promo_v_accessible,
        normalize_prizm_key,
    )

    prizm_key = normalize_prizm_key(inputs.prizm_segment)
    value_prizm = {
        "Simple Life",
        "Caregiving Households",
        "Unknown",
        "Kids and Cul-de-Sacs",
        "Aging in Place",
        "Wellness Seekers",
    }
    value_cohort = prizm_key in value_prizm or inputs.purchase_power_category in {"Low", "Medium"}
    lower_income = is_lower_income_context(
        zip_income_tier=inputs.zip_income_tier,
        purchase_power_category=inputs.purchase_power_category,
        premium_zip=inputs.premium_zip,
    )
    wellness = not segment_axis_is_pain(inputs.ceragem_segment) and inputs.pain_index_category != "High"
    pain_axis = segment_axis_is_pain(inputs.ceragem_segment) or inputs.pain_index_category in {"High", "Medium"}

    if pain_axis and is_promotion_active("Master V6"):
        v6_ok = is_post_promo_v_accessible(
            "Master V6",
            purchase_power_category=inputs.purchase_power_category,
            zip_income_tier=inputs.zip_income_tier,
        )
        if v6_ok and product in {"Master S4", "Master V5", "Master V7", "Master V6"}:
            return "Master V6"

    if pain_axis and is_promotion_active("Master V5"):
        v5_ok = is_post_promo_v_accessible(
            "Master V5",
            purchase_power_category=inputs.purchase_power_category,
            zip_income_tier=inputs.zip_income_tier,
        )
        if v5_ok and product in {"Master S4", "Master V5"}:
            return "Master V5"

    if segment_axis_is_pain(inputs.ceragem_segment) and inputs.pain_index_category == "High":
        return product

    if wellness and lower_income and value_cohort:
        if product in {STANDARD_VALUE_M_SKU, STANDARD_VALUE_S_SKU} and is_promotion_active("Pause M6s"):
            if inputs.lifestyle_category in {"Medium", "High"} or inputs.purchase_power_category == "Medium":
                return "Pause M6s"
        if product == STANDARD_VALUE_M_SKU and is_promotion_active(STANDARD_VALUE_S_SKU):
            if inputs.lifestyle_category == "Low":
                return STANDARD_VALUE_S_SKU

    if product == "Pause M6" and value_cohort and is_promotion_active("Pause M6s"):
        return "Pause M6s"

    if (
        product in {STANDARD_VALUE_M_SKU, "Pause M6", "Pause M6s"}
        and wellness
        and lower_income
        and is_promotion_active(STANDARD_VALUE_S_SKU)
        and inputs.lifestyle_category == "Low"
    ):
        return STANDARD_VALUE_S_SKU

    if (
        product == STANDARD_VALUE_M_SKU
        and wellness
        and lower_income
        and is_promotion_active(STANDARD_VALUE_S_SKU)
    ):
        return STANDARD_VALUE_S_SKU

    if (
        wellness
        and is_promotion_active("Pause M10")
        and is_m10_eligible_zip(
            premium_zip=inputs.premium_zip,
            zip_income_tier=inputs.zip_income_tier,
            purchase_power_category=inputs.purchase_power_category,
        )
        and product in {"Pause M4", "Pause M6", "Pause M6s"}
    ):
        return "Pause M10"

    return product


def _apply_v9_independent_nudge(product: str, inputs: RecommendationInputs, ladder: list[str]) -> str:
    """Master V9 stays on flagship geo — never swapped to Pause M10 (independent V-line path)."""
    return product


def _apply_m10_wellness_nudge(product: str, inputs: RecommendationInputs, ladder: list[str]) -> str:
    """M-series wellness path — Pause M10 nationwide when High PP + High/Mid income."""
    from app.intelligence.product_ladders import is_m10_eligible_zip

    if segment_axis_is_pain(inputs.ceragem_segment) or inputs.pain_index_category == "High":
        return product
    if "Pause M10" not in ladder:
        return product
    if not is_m10_eligible_zip(
        premium_zip=inputs.premium_zip,
        zip_income_tier=inputs.zip_income_tier,
        purchase_power_category=inputs.purchase_power_category,
    ):
        return product
    if product in {"Pause M6", "Pause M6s", "Pause M4"}:
        return "Pause M10"
    return product


def _apply_priority_market_nudges(product: str, inputs: RecommendationInputs, ladder: list[str]) -> str:
    """S4 promo expansion nationwide (all states/metros/ZIPs) when S4 promo is active."""
    from app.commercial.promotion_policy import is_promotion_active
    from app.intelligence.product_ladders import (
        is_m10_eligible_zip,
        normalize_prizm_key,
        STANDARD_VALUE_S_SKU,
    )

    if segment_axis_is_pain(inputs.ceragem_segment) or inputs.pain_index_category == "High":
        return product

    if not is_promotion_active(STANDARD_VALUE_S_SKU):
        return product

    prizm_key = normalize_prizm_key(inputs.prizm_segment)
    if inputs.purchase_power_category in {"Low", "Medium"}:
        if product in {"Pause M4", "Pause M6", "Pause M6s", "Master S4"} and STANDARD_VALUE_S_SKU in ladder:
            return STANDARD_VALUE_S_SKU
        if (
            prizm_key in {"Simple Life", "Caregiving Households", "Kids and Cul-de-Sacs", "Aging in Place"}
            and product in {"Pause M6s", "Pause M6", "Pause M4"}
        ):
            return STANDARD_VALUE_S_SKU

    return product


def resolve_rule_065_product(
    inputs: RecommendationInputs,
    *,
    apply_sleep: bool = True,
    apply_resistance: bool = True,
) -> dict:
    """Shared Rule-065 pipeline — used by intelligence scoring and promo-aware dashboard floor."""
    from app.intelligence.product_ladders import pick_primary_from_ladder, resolve_active_ladder

    ladder, source = resolve_active_ladder(
        ceragem_segment=inputs.ceragem_segment,
        prizm_segment=inputs.prizm_segment,
        pain_index_category=inputs.pain_index_category,
        premium_zip=inputs.premium_zip,
    )
    product = pick_primary_from_ladder(
        ladder,
        source=source,
        prizm_segment=inputs.prizm_segment,
        purchase_power_category=inputs.purchase_power_category,
        lifestyle_category=inputs.lifestyle_category,
        zip_income_tier=inputs.zip_income_tier,
        customer_state=inputs.customer_state,
        pain_index_category=inputs.pain_index_category,
        ceragem_segment=inputs.ceragem_segment,
        premium_zip=inputs.premium_zip,
    )
    product = _apply_v9_independent_nudge(product, inputs, ladder)
    product = _apply_m10_wellness_nudge(product, inputs, ladder)
    product = _apply_priority_market_nudges(product, inputs, ladder)
    product = _apply_standing_promo_primary(product, inputs)

    from app.intelligence.promotion_convert import apply_promo_convert_matrix

    product = apply_promo_convert_matrix(product, inputs, ladder)

    from app.intelligence.sku_migration import apply_sku_migration

    product = apply_sku_migration(product, inputs)

    from app.intelligence.v_m_anchor import apply_v_m_anchor_nudge

    product = apply_v_m_anchor_nudge(product, inputs, ladder)

    adjustment = {"adjusted_product": product, "adjusted": False, "adjustment_reason": "skipped"}
    sleep_adjustment = {
        "adjusted_product": product,
        "adjusted": False,
        "adjustment_reason": "skipped",
    }

    if apply_resistance:
        from app.commercial.engine import adjust_product_for_price_resistance

        adjustment = adjust_product_for_price_resistance(
            product,
            inputs.price_resistance_score,
            ceragem_segment=inputs.ceragem_segment,
            pain_index_category=inputs.pain_index_category,
            preserve_value_floor=_protect_value_massage(product, inputs),
        )
        product = adjustment["adjusted_product"]

    if apply_sleep:
        sleep_adjustment = adjust_product_for_sleep_deprivation(product, inputs)
        product = sleep_adjustment["adjusted_product"]

    return {
        "recommended_product": product,
        "price": PRODUCT_PRICES.get(product, 5499.0),
        "ladder_source": source,
        "product_ladder": ladder,
        "price_resistance_adjustment": adjustment,
        "sleep_deprivation_adjustment": sleep_adjustment,
    }


def adjust_product_for_sleep_deprivation(product: str, inputs: RecommendationInputs) -> dict:
    """
    Nudge recommendations toward Pause M Series in sleep-deprived metros.

    Therapeutic V Series (Pain High) is preserved; rest/wellness SKUs gain M-series weight.
    Source: Innerbody 2026 sleep-deprived city rankings.
    """
    boost = float(inputs.sleep_geo_boost or 0.0)
    if boost < 0.14:
        return {
            "original_product": product,
            "adjusted_product": product,
            "sleep_geo_boost": boost,
            "sleep_deprivation_tier": inputs.sleep_deprivation_tier,
            "adjustment_reason": "no_sleep_geo_signal",
            "adjusted": False,
        }

    if _protect_value_massage(product, inputs):
        return {
            "original_product": product,
            "adjusted_product": product,
            "sleep_geo_boost": boost,
            "sleep_deprivation_tier": inputs.sleep_deprivation_tier,
            "sleep_segment": inputs.sleep_segment,
            "adjustment_reason": "value_massage_preserved",
            "adjusted": False,
        }

    pain = inputs.pain_index_category
    preferred = _preferred_pause_m_series(
        inputs.purchase_power_category,
        inputs.lifestyle_category,
        premium_zip=inputs.premium_zip,
        zip_income_tier=inputs.zip_income_tier,
    )
    adjusted = product
    reason = "no_adjustment"

    if pain == "High" and product in _THERAPEUTIC_V_PRODUCTS:
        reason = "therapeutic_v_preserved"
    elif segment_axis_is_pain(inputs.ceragem_segment) and product in _THERAPEUTIC_V_PRODUCTS:
        reason = "fda_v_preserved_pain_segment"
    elif product == "Master S4":
        adjusted = "Pause M4" if boost >= 0.14 else product
        reason = "sleep_city_s4_to_m4"
    elif boost >= 0.24:
        if product.startswith("Pause M"):
            upgraded = _max_pause_m_series(product, preferred)
            if upgraded != product:
                adjusted = upgraded
                reason = "tier1_sleep_m_series_upgrade"
        elif product in {"Master S4", "Master V5", "Master V6"} and not segment_axis_is_pain(inputs.ceragem_segment):
            adjusted = preferred
            reason = "tier1_sleep_m_series_preferred"
        elif product == "Master V7" and inputs.lifestyle_category == "Low":
            adjusted = preferred
            reason = "tier1_sleep_wellness_shift"
    elif boost >= 0.14 and product in {"Master S4", "Master V5"}:
        if product in _THERAPEUTIC_V_PRODUCTS and segment_axis_is_pain(inputs.ceragem_segment):
            reason = "fda_v_preserved_pain_segment"
        elif product != "Master S4":
            adjusted = preferred
            reason = "tier2_sleep_m_series_preferred"
        else:
            adjusted = "Pause M4"
            reason = "tier2_sleep_m_series_preferred"

    return {
        "original_product": product,
        "adjusted_product": adjusted,
        "sleep_geo_boost": boost,
        "sleep_deprivation_tier": inputs.sleep_deprivation_tier,
        "sleep_segment": inputs.sleep_segment,
        "adjustment_reason": reason,
        "adjusted": adjusted != product,
    }


def build_recommendation_inputs(ctx) -> RecommendationInputs:
    zip_intel = ctx.zip_intelligence or {}
    customer = getattr(ctx, "customer", None) or {}
    return RecommendationInputs(
        ceragem_segment=ctx.ceragem_segment or "Mid-Low+ · Wellness",
        prizm_segment=ctx.prizm_proxy_segment or "Unknown",
        purchase_power_category=ctx.purchase_power_category or "Low",
        pain_index_category=ctx.pain_index_category or "Low",
        lifestyle_category=ctx.lifestyle_category or "Low",
        message_direction=ctx.message_direction or "Product Education Message",
        email_response_index=ctx.email_response_index,
        premium_zip=bool(zip_intel.get("premium_zip_indicator")),
        customer_state=customer.get("state") if isinstance(customer, dict) else None,
        zip_income_tier=str(zip_intel.get("income_tier") or "Unknown"),
        zip_purchase_potential=float(zip_intel.get("purchase_potential_score") or 0.0),
        price_resistance_score=float(getattr(ctx, "price_resistance_score", 0) or 0),
        sleep_geo_boost=float(zip_intel.get("sleep_geo_boost") or 0.0),
        sleep_deprivation_tier=str(zip_intel.get("sleep_deprivation_tier") or "none"),
        sleep_segment=str(zip_intel.get("sleep_segment") or "none"),
        customer_id=str(customer.get("customer_id") or "") if isinstance(customer, dict) else None,
    )


def rule_065_product_recommendation(inputs: RecommendationInputs) -> dict:
    """Rule-065: Ceragem + PRIZM product ladders → primary SKU (with resistance/sleep nudges)."""
    return resolve_rule_065_product(inputs, apply_sleep=True, apply_resistance=True)


def rule_066_campaign_priority(inputs: RecommendationInputs) -> dict:
    """Rule-066: High / Medium / Low from PP, lifestyle, pain, email responsiveness."""
    score = 0.0
    pp_map = {"High": 0.35, "Medium": 0.22, "Low": 0.1}
    ls_map = {"High": 0.25, "Medium": 0.15, "Low": 0.08}
    pain_map = {"High": 0.2, "Medium": 0.12, "Low": 0.05}
    score += pp_map.get(inputs.purchase_power_category, 0.1)
    score += ls_map.get(inputs.lifestyle_category, 0.08)
    score += pain_map.get(inputs.pain_index_category, 0.05)
    score += min(0.2, inputs.email_response_index * 0.2)
    score += min(0.08, float(inputs.sleep_geo_boost or 0.0) * 0.25)

    if score >= 0.65:
        priority = "High"
    elif score >= 0.35:
        priority = "Medium"
    else:
        priority = "Low"

    return {
        "campaign_priority": priority,
        "campaign_priority_score": PRIORITY_TO_SCORE[priority],
        "composite_score": round(score, 4),
    }


def rule_067_campaign_strategy(inputs: RecommendationInputs) -> dict:
    """Rule-067: Strategy follows Ceragem tier + axis."""
    tier = parse_ceragem_tier(inputs.ceragem_segment)
    pain_axis = segment_axis_is_pain(inputs.ceragem_segment)
    strategy_map = {
        ("High+", False): "Premium Campaign",
        ("High+", True): "Consultation Campaign",
        ("Mid-High+", False): "Wellness Campaign",
        ("Mid-High+", True): "Consultation Campaign",
        ("Mid+", False): "Wellness Campaign",
        ("Mid+", True): "Financing Campaign",
        ("Mid-Low+", False): "Educational Campaign",
        ("Mid-Low+", True): "Financing Campaign",
        ("Low+", False): "Educational Campaign",
        ("Low+", True): "Financing Campaign",
    }
    strategy = strategy_map.get((tier, pain_axis), "Wellness Campaign")
    if "Financing" in inputs.message_direction:
        strategy = "Financing Campaign"
    elif "Premium" in inputs.message_direction:
        strategy = "Premium Campaign"
    return {
        "campaign_strategy": strategy,
        "communication_strategy": inputs.message_direction,
    }


def evaluate_recommendation(inputs: RecommendationInputs) -> dict:
    product = rule_065_product_recommendation(inputs)
    priority = rule_066_campaign_priority(inputs)
    strategy = rule_067_campaign_strategy(inputs)
    return {"product": product, "priority": priority, "strategy": strategy}
