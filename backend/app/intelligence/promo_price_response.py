"""Post-promo final price responsiveness — analytical SSOT for outreach / convert / coverage.

Use this module when reasoning about how standing promotions change the consumer-facing
price and which promo SKU a cohort can realistically reach (up-convert, down-convert,
or keep). Promotion Coverage uses **conservative reach** per SKU: direct + segment-in
(M10) + ↑/↓ only when the primary SKU is not post-promo accessible (afford-own gate).
Cohorts that afford their own tier are tracked as unassigned. Opportunity Radar is
unchanged. See ``aggregate_conservative_promo_coverage``.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import func

from app.commercial.engine import PRICE_RESISTANCE_DOWNGRADE, effective_customer_payment
from app.commercial.promotion_policy import is_promotion_active, standing_promo_product_order
from app.intelligence.ceragem_rules import parse_ceragem_axis, parse_ceragem_tier, segment_axis_is_pain
from app.intelligence.promotion_policy_constants import (
    PP_ACCESSIBILITY_AFFLUENT_MIN_PRICE,
    PP_ACCESSIBILITY_HIGH_MIN_PRICE,
    PP_ACCESSIBILITY_LOW_MAX_PRICE,
    PP_ACCESSIBILITY_MID_HIGH_MAX_PRICE,
    PP_ACCESSIBILITY_MID_HIGH_MIN_PRICE,
    PP_ACCESSIBILITY_MID_LOW_MAX_PRICE,
    PP_ACCESSIBILITY_MID_MAX_PRICE,
    V_POST_PROMO_LOW_PP_MAX_PRICE,
    V_POST_PROMO_MID_PP_MAX_PRICE,
    V_VALUE_ENTRY_SKU,
)
from app.intelligence.product_ladders import _purchase_power_score
from app.reference.registry import normalize_product_code

_PP_CATEGORY_TO_ZIP_TIER = {"Low": "Lower", "Medium": "Mid", "High": "High"}


class PromoPriceDirection(str, Enum):
    KEEP = "keep"
    UP = "up_convert"
    DOWN = "down_convert"
    UNREACHABLE = "unreachable"


@dataclass(frozen=True)
class PromoPriceResponse:
    """Analytical outcome for one primary SKU + cohort profile."""

    primary_sku: str
    outreach_sku: str
    direction: PromoPriceDirection
    effective_price: float
    accessible: bool
    purchase_power_score: float
    accessibility_fit: float
    reason: str


def effective_post_promo_price(product_code: str) -> float:
    """Consumer-facing price after active standing promo (else catalog gross)."""
    return effective_customer_payment(normalize_product_code(product_code))


def purchase_power_score(
    purchase_power_category: str | None,
    zip_income_tier: str | None = None,
) -> float:
    tier = zip_income_tier or _PP_CATEGORY_TO_ZIP_TIER.get((purchase_power_category or "").strip(), "Mid")
    return _purchase_power_score((purchase_power_category or "Medium").strip(), tier)


def zip_income_tier_from_pp_category(purchase_power_category: str | None) -> str:
    return _PP_CATEGORY_TO_ZIP_TIER.get((purchase_power_category or "").strip(), "Mid")


def accessibility_fit(product_code: str, purchase_power_score: float) -> float:
    """Signed fit score: higher = better post-promo price match for the cohort."""
    price = effective_post_promo_price(product_code)
    if purchase_power_score < 38:
        if price <= PP_ACCESSIBILITY_LOW_MAX_PRICE:
            return 9.0
        if price <= PP_ACCESSIBILITY_MID_LOW_MAX_PRICE:
            return 6.0
        if price <= PP_ACCESSIBILITY_MID_MAX_PRICE:
            return 2.0
        return -5.0
    if purchase_power_score < 58:
        if PP_ACCESSIBILITY_MID_HIGH_MIN_PRICE <= price <= PP_ACCESSIBILITY_MID_HIGH_MAX_PRICE:
            return 5.0
        if price <= PP_ACCESSIBILITY_MID_LOW_MAX_PRICE:
            return 4.0
        return 0.0
    if price >= PP_ACCESSIBILITY_AFFLUENT_MIN_PRICE:
        return 8.0
    if price >= PP_ACCESSIBILITY_HIGH_MIN_PRICE:
        return 5.0
    return 1.0


def is_post_promo_accessible(
    product_code: str,
    *,
    purchase_power_category: str | None = None,
    zip_income_tier: str | None = None,
    purchase_power_score: float | None = None,
) -> bool:
    """Whether the cohort can reach this SKU at its post-promo consumer price."""
    product = normalize_product_code(product_code)
    if not is_promotion_active(product):
        return accessibility_fit(product, purchase_power_score or purchase_power_score_from(
            purchase_power_category, zip_income_tier
        )) > 0

    pp = purchase_power_score if purchase_power_score is not None else purchase_power_score_from(
        purchase_power_category, zip_income_tier
    )
    price = effective_post_promo_price(product)

    # V-line standing promos — preserve legacy boolean gate used in recommendation_rules.
    if product in {"Master V5", "Master V6", "Master V7"}:
        promo_product = "Master V6" if product == "Master V7" else product
        if not is_promotion_active(promo_product) and product == "Master V7":
            return False
        if pp < 38:
            return price <= V_POST_PROMO_LOW_PP_MAX_PRICE
        if pp < 58:
            return price <= V_POST_PROMO_MID_PP_MAX_PRICE
        return True

    return accessibility_fit(product, pp) > 0


def purchase_power_score_from(
    purchase_power_category: str | None,
    zip_income_tier: str | None,
) -> float:
    return purchase_power_score(purchase_power_category, zip_income_tier)


def _best_standing_promo_in_ladder(
    candidates: list[str],
    *,
    purchase_power_score: float,
) -> str | None:
    standing = set(standing_promo_product_order())
    best: tuple[float, str] | None = None
    for code in candidates:
        if code not in standing or not is_promotion_active(code):
            continue
        fit = accessibility_fit(code, purchase_power_score)
        if fit <= 0:
            continue
        if best is None or fit > best[0]:
            best = (fit, code)
    return best[1] if best else None


def _walk_down_to_accessible_standing_promo(
    product: str,
    *,
    purchase_power_score: float,
    max_steps: int = 4,
) -> tuple[str, PromoPriceDirection, str]:
    current = product
    for _ in range(max_steps):
        if is_promotion_active(current) and is_post_promo_accessible(
            current, purchase_power_score=purchase_power_score
        ):
            if current == product:
                return current, PromoPriceDirection.KEEP, "post_promo_price_accessible"
            return current, PromoPriceDirection.DOWN, "down_convert_post_promo_price"
        nxt = PRICE_RESISTANCE_DOWNGRADE.get(current)
        if not nxt or nxt == current:
            break
        current = nxt
    fallback = _best_standing_promo_in_ladder([product, *PRICE_RESISTANCE_DOWNGRADE.values()], purchase_power_score=purchase_power_score)
    if fallback:
        direction = PromoPriceDirection.KEEP if fallback == product else PromoPriceDirection.DOWN
        return fallback, direction, "nearest_accessible_standing_promo"
    return product, PromoPriceDirection.UNREACHABLE, "no_accessible_standing_promo"


def _up_convert_candidates(primary: str, *, pain_axis: bool) -> list[str]:
    if not pain_axis:
        return []
    if primary == V_VALUE_ENTRY_SKU:
        return ["Master V6", "Master V5"]
    if primary in {"Master V7", "Master V9"}:
        return ["Master V6", "Master V5"]
    return []


def resolve_promo_price_response(
    primary_sku: str,
    *,
    purchase_power_category: str | None = None,
    zip_income_tier: str | None = None,
    ceragem_segment: str | None = None,
) -> PromoPriceResponse:
    """
    Map a standard (primary) SKU + cohort to the standing-promo SKU implied by
    post-promo consumer price — up-convert, down-convert, or keep.
    """
    primary = normalize_product_code((primary_sku or "").strip())
    zip_tier = zip_income_tier or zip_income_tier_from_pp_category(purchase_power_category)
    pp_score = purchase_power_score(purchase_power_category, zip_tier)
    pain_axis = segment_axis_is_pain(ceragem_segment or "") or parse_ceragem_axis(ceragem_segment or "") == "Pain Index"

    # Pain-axis up-convert (e.g. S4 → V6/V5) before keeping value-entry promo SKU.
    for candidate in _up_convert_candidates(primary, pain_axis=pain_axis):
        if is_promotion_active(candidate) and is_post_promo_accessible(
            candidate,
            purchase_power_category=purchase_power_category,
            zip_income_tier=zip_tier,
        ):
            price = effective_post_promo_price(candidate)
            return PromoPriceResponse(
                primary_sku=primary,
                outreach_sku=candidate,
                direction=PromoPriceDirection.UP,
                effective_price=price,
                accessible=True,
                purchase_power_score=pp_score,
                accessibility_fit=accessibility_fit(candidate, pp_score),
                reason="up_convert_post_promo_price",
            )

    # Active standing promo on primary — keep if affordable, else step down (e.g. V6 → V5).
    if primary in set(standing_promo_product_order()) and is_promotion_active(primary):
        outreach, direction, reason = _walk_down_to_accessible_standing_promo(primary, purchase_power_score=pp_score)
        price = effective_post_promo_price(outreach)
        return PromoPriceResponse(
            primary_sku=primary,
            outreach_sku=outreach,
            direction=direction,
            effective_price=price,
            accessible=direction != PromoPriceDirection.UNREACHABLE,
            purchase_power_score=pp_score,
            accessibility_fit=accessibility_fit(outreach, pp_score),
            reason=reason,
        )

    # Non-promo primary mapped to nearest accessible standing promo (outreach fallback).
    outreach, direction, reason = _walk_down_to_accessible_standing_promo(primary, purchase_power_score=pp_score)
    price = effective_post_promo_price(outreach)
    return PromoPriceResponse(
        primary_sku=primary,
        outreach_sku=outreach,
        direction=direction if outreach != primary else PromoPriceDirection.KEEP,
        effective_price=price,
        accessible=direction != PromoPriceDirection.UNREACHABLE,
        purchase_power_score=pp_score,
        accessibility_fit=accessibility_fit(outreach, pp_score),
        reason=reason,
    )


def aggregate_price_responsive_promo_coverage(
    cohort_rows: list[dict],
) -> dict[str, dict[str, int | float]]:
    """
    Project standing-promo coverage from primary SKU cohorts + PP/segment context.

    Each row: {product, customers, purchase_power_category?, zip_income_tier?, ceragem_segment?}
    Returns per standing promo SKU:
      customers, direct, up_convert, down_convert, avg_accessibility_fit
    """
    totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {"customers": 0.0, "direct": 0.0, "up_convert": 0.0, "down_convert": 0.0, "fit_sum": 0.0}
    )
    for row in cohort_rows:
        primary = normalize_product_code(str(row.get("product") or ""))
        customers = int(row.get("customers") or 0)
        if not primary or customers <= 0:
            continue
        response = resolve_promo_price_response(
            primary,
            purchase_power_category=row.get("purchase_power_category"),
            zip_income_tier=row.get("zip_income_tier"),
            ceragem_segment=row.get("ceragem_segment"),
        )
        outreach = response.outreach_sku
        bucket = totals[outreach]
        bucket["customers"] += customers
        bucket["fit_sum"] += customers * response.accessibility_fit
        if response.direction == PromoPriceDirection.UP:
            bucket["up_convert"] += customers
        elif response.direction == PromoPriceDirection.DOWN:
            bucket["down_convert"] += customers
        elif response.primary_sku == outreach:
            bucket["direct"] += customers

    result: dict[str, dict[str, int | float]] = {}
    for product, bucket in totals.items():
        customers = int(bucket["customers"])
        result[product] = {
            "customers": customers,
            "direct": int(bucket["direct"]),
            "up_convert": int(bucket["up_convert"]),
            "down_convert": int(bucket["down_convert"]),
            "avg_accessibility_fit": round(bucket["fit_sum"] / customers, 3) if customers else 0.0,
        }
    return result


def eligible_m10_segment_coverage(
    primary_sku: str,
    *,
    purchase_power_category: str | None = None,
    ceragem_segment: str | None = None,
) -> bool:
    """True when a cohort should reach Pause M10 via Coverage segment-in (not price ladder)."""
    primary = normalize_product_code((primary_sku or "").strip())
    if not primary:
        return False
    tier = parse_ceragem_tier(ceragem_segment or "")
    axis = parse_ceragem_axis(ceragem_segment or "")
    pp = (purchase_power_category or "").strip()
    if tier == "High+" and axis == "Wellness" and pp == "High" and primary in {"Master V9", "Master V7"}:
        return True
    if primary in {"Pause M6", "Pause M6s"}:
        from app.campaign.standing_promo_demand import standing_promo_outreach_product

        return standing_promo_outreach_product(primary, purchase_power=pp or None, ceragem_segment=ceragem_segment) == "Pause M10"
    return False


def aggregate_conservative_promo_coverage(
    cohort_rows: list[dict],
) -> tuple[dict[str, dict[str, int | float]], dict[str, int]]:
    """
    Conservative Promotion Coverage reach — at most one standing-promo SKU per cohort row.

    - Pause M10: segment-in (S) for wellness-premium V9/V7 (+ pause-map donors) when accessible.
    - Other standing promos: direct keep, or ↑/↓ only when the primary SKU is not post-promo
      accessible (afford-own gate).
    - Remaining cohorts (afford own tier, unreachable, non-standing outreach) → unassigned.
    """
    standing = set(standing_promo_product_order())
    totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "customers": 0.0,
            "direct": 0.0,
            "up_convert": 0.0,
            "down_convert": 0.0,
            "segment_in": 0.0,
            "fit_sum": 0.0,
        }
    )
    unassigned = {"customers": 0, "afford_own": 0, "unreachable": 0}

    for row in cohort_rows:
        primary = normalize_product_code(str(row.get("product") or ""))
        customers = int(row.get("customers") or 0)
        if not primary or customers <= 0:
            continue
        pp = row.get("purchase_power_category")
        zip_tier = row.get("zip_income_tier")
        segment = row.get("ceragem_segment")

        if (
            "Pause M10" in standing
            and is_promotion_active("Pause M10")
            and eligible_m10_segment_coverage(primary, purchase_power_category=pp, ceragem_segment=segment)
            and is_post_promo_accessible("Pause M10", purchase_power_category=pp, zip_income_tier=zip_tier)
        ):
            bucket = totals["Pause M10"]
            bucket["customers"] += customers
            bucket["segment_in"] += customers
            pp_score = purchase_power_score(pp, zip_tier or zip_income_tier_from_pp_category(pp))
            bucket["fit_sum"] += customers * accessibility_fit("Pause M10", pp_score)
            continue

        response = resolve_promo_price_response(
            primary,
            purchase_power_category=pp,
            zip_income_tier=zip_tier,
            ceragem_segment=segment,
        )
        outreach = normalize_product_code(response.outreach_sku)

        if response.direction in {PromoPriceDirection.UP, PromoPriceDirection.DOWN}:
            if is_post_promo_accessible(
                primary,
                purchase_power_category=pp,
                zip_income_tier=zip_tier,
            ):
                unassigned["customers"] += customers
                unassigned["afford_own"] += customers
                continue

        if response.direction == PromoPriceDirection.UNREACHABLE or outreach not in standing:
            unassigned["customers"] += customers
            unassigned["unreachable"] += customers
            continue

        bucket = totals[outreach]
        bucket["customers"] += customers
        bucket["fit_sum"] += customers * response.accessibility_fit
        if response.direction == PromoPriceDirection.UP:
            bucket["up_convert"] += customers
        elif response.direction == PromoPriceDirection.DOWN:
            bucket["down_convert"] += customers
        elif response.primary_sku == outreach:
            bucket["direct"] += customers

    result: dict[str, dict[str, int | float]] = {}
    for product, bucket in totals.items():
        customers = int(bucket["customers"])
        result[product] = {
            "customers": customers,
            "direct": int(bucket["direct"]),
            "up_convert": int(bucket["up_convert"]),
            "down_convert": int(bucket["down_convert"]),
            "segment_in": int(bucket["segment_in"]),
            "avg_accessibility_fit": round(bucket["fit_sum"] / customers, 3) if customers else 0.0,
        }
    return result, unassigned


def aggregate_hybrid_promo_coverage(
    cohort_rows: list[dict],
) -> dict[str, dict[str, int | float]]:
    """Backward-compatible alias — returns SKU totals only (legacy hybrid callers)."""
    skus, _ = aggregate_conservative_promo_coverage(cohort_rows)
    return skus


_BAND_TO_PP_CATEGORY: dict[str, str] = {
    "<$50K": "Low",
    "$50K–$75K": "Low",
    "$75K–$100K": "Medium",
    "$100K–$150K": "High",
    "$150K+": "High",
}


def purchase_power_category_from_index(purchase_power_index: float | None) -> str:
    value = float(purchase_power_index if purchase_power_index is not None else 0.45)
    if value < 0.34:
        return "Low"
    if value < 0.67:
        return "Medium"
    return "High"


def _cohort_rows_from_rollups(db, upload_id) -> list[dict]:
    from app.acquisition.rollup import ROLLUP_KEY_SEP, has_distribution_rollups
    from app.models.scale import UploadRollup

    if not has_distribution_rollups(db, upload_id):
        return []

    if upload_id:
        ceragem_prod_q = db.query(UploadRollup.key, UploadRollup.customer_count).filter(
            UploadRollup.upload_id == upload_id,
            UploadRollup.dimension == "ceragem_prod",
        )
        pp_band_prod_q = db.query(UploadRollup.key, UploadRollup.customer_count).filter(
            UploadRollup.upload_id == upload_id,
            UploadRollup.dimension == "pp_band_prod",
        )
    else:
        ceragem_prod_q = (
            db.query(UploadRollup.key, func.sum(UploadRollup.customer_count))
            .filter(UploadRollup.dimension == "ceragem_prod")
            .group_by(UploadRollup.key)
        )
        pp_band_prod_q = (
            db.query(UploadRollup.key, func.sum(UploadRollup.customer_count))
            .filter(UploadRollup.dimension == "pp_band_prod")
            .group_by(UploadRollup.key)
        )

    product_pp: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for composite_key, count in pp_band_prod_q.all():
        parts = str(composite_key or "").split(ROLLUP_KEY_SEP, 1)
        if len(parts) != 2:
            continue
        band, product = parts
        code = normalize_product_code(product)
        if not code:
            continue
        product_pp[code][str(band)] += int(count or 0)

    rows: list[dict] = []
    for composite_key, count in ceragem_prod_q.all():
        parts = str(composite_key or "").split(ROLLUP_KEY_SEP, 1)
        if len(parts) != 2:
            continue
        segment, product = parts
        code = normalize_product_code(product)
        customers = int(count or 0)
        if not code or customers <= 0:
            continue

        pp_counts = product_pp.get(code)
        if not pp_counts:
            rows.append(
                {
                    "product": code,
                    "customers": customers,
                    "purchase_power_category": "Medium",
                    "ceragem_segment": str(segment or "").strip() or None,
                }
            )
            continue

        total_pp = sum(pp_counts.values()) or 1
        remaining = customers
        band_items = sorted(pp_counts.items(), key=lambda item: -item[1])
        for index, (band, band_count) in enumerate(band_items):
            if index == len(band_items) - 1:
                allocated = remaining
            else:
                allocated = int(round(customers * band_count / total_pp))
                remaining -= allocated
            if allocated <= 0:
                continue
            rows.append(
                {
                    "product": code,
                    "customers": allocated,
                    "purchase_power_category": _BAND_TO_PP_CATEGORY.get(str(band), "Medium"),
                    "ceragem_segment": str(segment or "").strip() or None,
                }
            )
    return rows


def _cohort_rows_from_intelligence(db, upload_id) -> list[dict]:
    from sqlalchemy import case

    from app.models.customer import Customer, CustomerIntelligence

    pp_case = case(
        (CustomerIntelligence.purchase_power_index < 0.34, "Low"),
        (CustomerIntelligence.purchase_power_index < 0.67, "Medium"),
        else_="High",
    )
    q = db.query(
        CustomerIntelligence.ceragem_segment,
        CustomerIntelligence.recommended_product,
        pp_case.label("pp_category"),
        func.count(CustomerIntelligence.id),
    ).join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    q = q.filter(CustomerIntelligence.recommended_product.isnot(None)).group_by(
        CustomerIntelligence.ceragem_segment,
        CustomerIntelligence.recommended_product,
        pp_case,
    )

    rows: list[dict] = []
    for segment, product, pp_category, count in q.all():
        code = normalize_product_code(str(product or ""))
        customers = int(count or 0)
        if not code or customers <= 0:
            continue
        rows.append(
            {
                "product": code,
                "customers": customers,
                "purchase_power_category": str(pp_category or "Medium"),
                "ceragem_segment": str(segment or "").strip() or None,
            }
        )
    return rows


def load_promo_coverage_cohort_rows(db, upload_id) -> list[dict]:
    """Segment × product × PP cohorts for post-promo price coverage analysis."""
    if not hasattr(db, "query"):
        return []
    rows = _cohort_rows_from_rollups(db, upload_id)
    if rows:
        return rows
    return _cohort_rows_from_intelligence(db, upload_id)
