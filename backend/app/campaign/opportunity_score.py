"""State-level Opportunity Score for Mission Control / Finder radar."""

from __future__ import annotations

from app.campaign.standing_promo_demand import standing_promo_outreach_product
from app.commercial.engine import effective_customer_payment
from app.commercial.promotion_policy import is_promotion_active, promotion_pct
from app.intelligence.ceragem_rules import parse_ceragem_tier
from app.reference.registry import ACTIVE_PRODUCT_CODES

_CERAGEM_TIER_PURCHASE_POWER_SCORE: dict[str, float] = {
    "High+": 90.0,
    "Mid-High+": 70.0,
    "Mid+": 58.0,
    "Mid-Low+": 45.0,
    "Low+": 25.0,
}

AXIS_SPREAD_FLOOR = 18.0
AXIS_SPREAD_CEILING = 92.0

def _product_default_promo_pct(product: str) -> float:
    return promotion_pct(product) if is_promotion_active(product) else 0.0

_PREMIUM_PRODUCTS = frozenset({"Master V9", "Master V7", "Pause M10"})
_VALUE_ENTRY_PRODUCTS = frozenset({"Pause M4", "Pause M6", "Pause M6s", "Master S4"})
_SERIES_FIT_CAP = 10.0


def spread_cohort_axis(
    values: list[float],
    *,
    floor: float = AXIS_SPREAD_FLOOR,
    ceiling: float = AXIS_SPREAD_CEILING,
) -> list[float]:
    """Stretch a tight cluster of axis scores for radar X-axis readability."""
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    span = hi - lo
    if span < 0.5:
        mid = round((floor + ceiling) / 2, 1)
        return [mid] * len(values)
    stretched_values: list[float] = []
    for raw in values:
        rank = (raw - lo) / span
        stretched = rank**0.85
        stretched_values.append(round(floor + stretched * (ceiling - floor), 1))
    return stretched_values


def apply_radar_axis_spreads(rows: list[dict]) -> list[dict]:
    """Widen intelligence X-axis scores (Pain, Lifestyle, PP, Brand, Digital) for radar readability."""
    if len(rows) < 2:
        return rows

    axis_keys = (
        "pain_index_score",
        "lifestyle_score",
        "purchase_power_score",
        "brand_score",
        "digital_score",
    )
    spread_map: dict[str, list[float]] = {}
    for key in axis_keys:
        raw_values = [float(row.get(key) or 0) for row in rows]
        spread_map[key] = spread_cohort_axis(raw_values)

    result: list[dict] = []
    for index, row in enumerate(rows):
        merged = dict(row)
        for key in axis_keys:
            merged[f"{key}_raw"] = round(float(row.get(key) or 0), 1)
            merged[key] = spread_map[key][index]
        result.append(merged)
    return result


def _intelligence_product(row: dict) -> str:
    """ZIP ranking uses intelligence SKU — not standing-promo outreach mapping."""
    return str(
        row.get("intelligence_product")
        or row.get("recommended_product")
        or row.get("top_product")
        or ""
    )


def _series_fit_bonus(intelligence_product: str | None, pain_score: float, lifestyle_score: float) -> float:
    """Balanced V / M / S intelligence fit — equal cap per series path."""
    product = intelligence_product or ""
    if product.startswith("Master V") and pain_score >= 38:
        return min(_SERIES_FIT_CAP, (pain_score - 33.0) * 0.16)
    if product.startswith("Pause M") and lifestyle_score >= 36:
        return min(_SERIES_FIT_CAP, (lifestyle_score - 31.0) * 0.14)
    if product == "Master S4":
        if pain_score < 42:
            return min(_SERIES_FIT_CAP, (42.0 - pain_score) * 0.14)
        if lifestyle_score >= 40:
            return min(_SERIES_FIT_CAP, lifestyle_score * 0.08)
    return 0.0


def _price_accessibility_fit(product: str, purchase_power_score: float) -> float:
    """Lower purchase-power geographies favor accessible effective (post-promo) prices."""
    from app.intelligence.promo_price_response import accessibility_fit

    return accessibility_fit(product, purchase_power_score)


def sellable_products_for_purchase_power_score(purchase_power_score: float, limit: int = 6) -> list[str]:
    """Active SKUs with positive price-accessibility fit for a purchase-power score (0–100)."""
    ranked = [
        (code, _price_accessibility_fit(code, purchase_power_score))
        for code in ACTIVE_PRODUCT_CODES
    ]
    return [code for code, fit in sorted(ranked, key=lambda item: -item[1]) if fit > 0][:limit]


def _product_series_code(product: str) -> str:
    if product.startswith("Master V") or product == "Master S4":
        return "v"
    if product.startswith("Pause M"):
        return "m"
    return "other"


product_series_code = _product_series_code


def purchase_power_score_from_ceragem_segment(segment: str | None) -> float:
    """Map Ceragem Segmentation+ tier to a purchase-power score for SKU accessibility."""
    return _CERAGEM_TIER_PURCHASE_POWER_SCORE.get(parse_ceragem_tier(segment), 50.0)


def recommendation_products_for_ceragem_segment(
    segment: str,
    top_recommended: list[str],
    *,
    limit: int = 6,
    min_v_series: int = 2,
    min_m_series: int = 2,
) -> list[str]:
    """Ceragem donut hover SKUs — explicit Ceragem product ladder, then observed counts."""
    from app.intelligence.product_ladders import ladder_for_ceragem, merge_ladder_with_observed

    ladder = ladder_for_ceragem(segment)
    ordered = merge_ladder_with_observed(ladder, top_recommended, limit=limit)
    # Guarantee a V/M mix for the widget when the ladder is series-skewed.
    if min_v_series or min_m_series:
        filled = recommendation_products_for_purchase_power_band(
            purchase_power_score_from_ceragem_segment(segment),
            ordered + list(top_recommended or []),
            limit=limit,
            min_v_series=min_v_series,
            min_m_series=min_m_series,
        )
        # Prefer ladder order, then fill gaps from the series-mix helper.
        return merge_ladder_with_observed(ordered, filled, limit=limit)
    return ordered


def recommendation_products_for_prizm_segment(
    segment: str,
    top_recommended: list[str],
    *,
    limit: int = 6,
) -> list[str]:
    """PRIZM hover SKUs — explicit PRIZM product ladder, then observed counts."""
    from app.intelligence.product_ladders import ladder_for_prizm, merge_ladder_with_observed

    return merge_ladder_with_observed(ladder_for_prizm(segment), top_recommended, limit=limit)


def recommendation_products_for_purchase_power_band(
    purchase_power_score: float,
    top_recommended: list[str],
    *,
    limit: int = 6,
    min_v_series: int = 2,
    min_m_series: int = 2,
) -> list[str]:
    """Band popup SKUs — at least min V-series and min M-series picks, then fill to limit."""
    sellable = sellable_products_for_purchase_power_score(purchase_power_score, limit=limit * 2)
    result: list[str] = []
    seen: set[str] = set()

    def append_from(candidates: list[str], series: str, max_count: int) -> int:
        added = 0
        for product in candidates:
            if added >= max_count or product in seen or _product_series_code(product) != series:
                continue
            seen.add(product)
            result.append(product)
            added += 1
        return added

    v_recommended = [p for p in top_recommended if _product_series_code(p) == "v"]
    m_recommended = [p for p in top_recommended if _product_series_code(p) == "m"]
    v_sellable = [p for p in sellable if _product_series_code(p) == "v"]
    m_sellable = [p for p in sellable if _product_series_code(p) == "m"]

    v_added = append_from(v_recommended, "v", min_v_series)
    if v_added < min_v_series:
        append_from(v_sellable, "v", min_v_series - v_added)

    m_added = append_from(m_recommended, "m", min_m_series)
    if m_added < min_m_series:
        append_from(m_sellable, "m", min_m_series - m_added)

    for product in top_recommended + sellable:
        if len(result) >= limit:
            break
        if product in seen:
            continue
        seen.add(product)
        result.append(product)

    return result[:limit]


def _lifestyle_product_fit(
    product: str,
    lifestyle_tier: str | None,
    lifestyle_score: float,
    pain_score: float,
) -> float:
    """Align SKU recommendations with lifestyle geography tiers."""
    tier = str(lifestyle_tier or "")
    fit = 0.0
    if "Premium Wellness" in tier:
        if product in _PREMIUM_PRODUCTS:
            fit += 7.0
        if product in {"Master S4", "Pause M4"}:
            fit -= 7.0
    elif "Lifestyle Wellness" in tier:
        if product.startswith("Master V") or product == "Master S4":
            fit += 5.0
        if product in {"Pause M4"}:
            fit -= 4.0
    elif "Therapeutic" in tier or pain_score >= 50:
        if product.startswith("Master V") or product == "Master S4":
            fit += 6.0
        if product == "Master S4":
            fit += 2.0
    elif lifestyle_score >= 58 and product.startswith("Master V"):
        fit += 3.0
    return fit


def _promotion_accessibility_fit(product: str, purchase_power_score: float) -> float:
    """Legacy promo bonus — superseded by effective_customer_payment in _price_accessibility_fit."""
    promo_pct = _product_default_promo_pct(product)
    if promo_pct <= 0:
        return 0.0
    if purchase_power_score < 45 and promo_pct >= 0.20:
        return min(8.0, promo_pct * 22)
    if purchase_power_score < 55 and promo_pct >= 0.18:
        return min(5.0, promo_pct * 14)
    return min(3.0, promo_pct * 8) if promo_pct >= 0.15 else 0.0


def _purchase_power_category(row: dict) -> str | None:
    explicit = row.get("purchase_power")
    if explicit in {"High", "Medium", "Low"}:
        return str(explicit)
    tier = str(row.get("purchase_power_tier") or "")
    if "High Income" in tier:
        return "High"
    if "Lower Income" in tier:
        return "Low"
    if "Mid Income" in tier:
        return "Medium"
    score = float(row.get("purchase_power_score") or row.get("purchase_power_index_score") or 0)
    if score >= 62:
        return "High"
    if score >= 42:
        return "Medium"
    return "Low"


def _outreach_product(row: dict) -> str:
    raw = row.get("top_product") or row.get("recommended_product") or ""
    return standing_promo_outreach_product(
        str(raw),
        purchase_power=_purchase_power_category(row),
        ceragem_segment=row.get("ceragem_segment"),
    ) or str(raw)


def _price_fit_product(row: dict) -> str:
    """Standing-promo outreach SKU for price fit (e.g. Pause M6 → Pause M6s)."""
    return _outreach_product(row)


def _product_opportunity_fit(row: dict) -> float:
    """BD product fit — series/lifestyle on intelligence SKU; price on outreach effective payment."""
    intelligence = str(row.get("top_product") or row.get("recommended_product") or "")
    price_product = _price_fit_product(row)
    pain = float(row.get("pain_index_score") or 0)
    lifestyle = float(row.get("lifestyle_score") or 0)
    purchase_power = float(row.get("purchase_power_score") or row.get("purchase_power_index_score") or 0)
    return (
        _series_fit_bonus(intelligence, pain, lifestyle)
        + _price_accessibility_fit(price_product, purchase_power)
        + _lifestyle_product_fit(intelligence, row.get("lifestyle_tier"), lifestyle, pain)
    )


def compute_state_opportunity_score(row: dict, *, max_revenue: float) -> float:
    """
    Blend geo-weighted intelligence axes, revenue share, conversion, and product fit.

    Product fit layers:
    - Series therapeutic / wellness alignment (V/M/S4) on intelligence SKU
    - Price accessibility vs effective post-promo payment on outreach SKU
    - Lifestyle geography tier alignment on intelligence SKU
    """
    conversion = float(row.get("conversion") or 0)
    revenue = float(row.get("revenue") or 0)
    revenue_share = revenue / max(max_revenue, 1.0)

    pain = float(row.get("pain_index_score") or 0)
    purchase_power = float(row.get("purchase_power_score") or row.get("purchase_power_index_score") or 0)
    lifestyle = float(row.get("lifestyle_score") or 0)
    brand = float(row.get("brand_score") or 0)
    digital = float(row.get("digital_score") or 0)

    intelligence_blend = (
        0.22 * pain
        + 0.20 * purchase_power
        + 0.18 * lifestyle
        + 0.20 * brand
        + 0.20 * digital
    )

    conversion_pts = min(99.0, conversion * 10000.0)
    product_fit = min(18.0, _product_opportunity_fit(row))

    score = (
        intelligence_blend * 0.55
        + revenue_share * 85.0 * 0.25
        + conversion_pts * 0.15
        + product_fit
    )
    return round(min(99.0, max(8.0, score)), 1)


_INDEX_LEVEL_PTS = {"High": 75.0, "Medium": 55.0, "Low": 25.0}


def compute_zip_opportunity_score(row: dict, *, max_revenue: float) -> float:
    """ZIP-level opportunity rank for Mission Control recent/top widgets."""
    purchase_power = float(
        row.get("purchase_power_index_score")
        or _INDEX_LEVEL_PTS.get(str(row.get("purchase_power") or ""), 45.0)
    )
    campaign_priority = float(
        row.get("campaign_priority_index_score")
        or _INDEX_LEVEL_PTS.get(str(row.get("campaign_priority") or ""), 45.0)
    )
    conversion = float(row.get("conversion") or 0)
    revenue_share = float(row.get("revenue") or 0) / max(max_revenue, 1.0)
    conversion_pts = min(99.0, conversion * 10000.0)
    pain = float(row.get("pain_index_score") or 45.0)
    lifestyle = float(row.get("lifestyle_index_score") or 45.0)
    series_fit = _series_fit_bonus(_intelligence_product(row), pain, lifestyle)
    intelligence_blend = (
        0.22 * float(row.get("pain_index_score") or 45.0)
        + 0.18 * float(row.get("lifestyle_index_score") or 45.0)
        + 0.20 * float(row.get("brand_index_score") or 45.0)
    )
    score = (
        0.24 * purchase_power
        + 0.18 * campaign_priority
        + 0.20 * revenue_share * 85.0
        + 0.12 * conversion_pts
        + series_fit * 0.5
        + intelligence_blend * 0.26
    )
    return round(min(99.0, max(8.0, score)), 1)
