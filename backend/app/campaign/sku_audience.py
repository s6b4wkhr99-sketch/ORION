"""Campaign SKU audience — Opportunity Finder / export use the same product-fit rule as Coverage."""

from __future__ import annotations

import uuid

from sqlalchemy import and_, case, func, literal, or_, update
from sqlalchemy.orm import Session

from app.intelligence.promo_price_response import assign_conservative_coverage
from app.models.customer import Customer, CustomerIntelligence
from app.reference.registry import PRODUCT_GROSS_SALES, normalize_product_code

S4_PRODUCT_ALIASES = ("Master S4", "Pause S4", "Master V4")
LOW_PP_INDEX_MAX = 0.34
CAMPAIGN_SKU_FILTER_VERSION = "v5-s4-pain-promo-reach-rev-v2"
AUDIENCE_MODE_RECOMMENDED = "recommended"
AUDIENCE_MODE_PROMO_REACH = "promo_reach"


def normalize_audience_mode(mode: str | None) -> str:
    value = (mode or AUDIENCE_MODE_RECOMMENDED).strip().lower().replace("-", "_")
    if value in {AUDIENCE_MODE_PROMO_REACH, "coverage", "promo"}:
        return AUDIENCE_MODE_PROMO_REACH
    return AUDIENCE_MODE_RECOMMENDED


def audience_mode_label(mode: str | None) -> str:
    return "Promo reach" if normalize_audience_mode(mode) == AUDIENCE_MODE_PROMO_REACH else "Recommended"


def customer_payment_map() -> dict[str, float]:
    """Gross if no promo, customer payment if a standing promo is active."""
    from app.commercial.engine import effective_customer_payment

    prices: dict[str, float] = {}
    for code in PRODUCT_GROSS_SALES:
        normalized = normalize_product_code(code)
        if not normalized:
            continue
        prices[normalized] = float(effective_customer_payment(normalized))
    s4 = prices.get("Master S4", 0.0)
    for alias in S4_PRODUCT_ALIASES:
        prices[alias] = s4
    return prices


def customer_payment_expr(product_expr):
    whens = [
        (product_expr == code, literal(price))
        for code, price in customer_payment_map().items()
        if price > 0
    ]
    if not whens:
        return literal(0.0)
    return case(*whens, else_=literal(0.0))


def priced_revenue_expr(product_expr):
    return func.coalesce(CustomerIntelligence.expected_conversion, 0.0) * customer_payment_expr(product_expr)


def confirmed_s4_pain_v5_clause():
    """S4 + Pain + Low PP → confirmed FDA V5 campaign target (same pocket as Coverage)."""
    return and_(
        CustomerIntelligence.recommended_product.in_(S4_PRODUCT_ALIASES),
        CustomerIntelligence.ceragem_segment.ilike("%Pain%"),
        CustomerIntelligence.purchase_power_index.isnot(None),
        CustomerIntelligence.purchase_power_index < LOW_PP_INDEX_MAX,
    )


def purchase_power_category_expr():
    return case(
        (CustomerIntelligence.purchase_power_index.is_(None), literal("Medium")),
        (CustomerIntelligence.purchase_power_index < 0.34, literal("Low")),
        (CustomerIntelligence.purchase_power_index < 0.67, literal("Medium")),
        else_=literal("High"),
    )


def expand_campaign_skus(skus: list[str]) -> list[str]:
    expanded: list[str] = []
    seen: set[str] = set()
    for raw in skus:
        code = normalize_product_code((raw or "").strip())
        if not code or code in seen:
            continue
        seen.add(code)
        expanded.append(code)
        if code == "Master S4":
            for alias in S4_PRODUCT_ALIASES:
                if alias not in seen:
                    seen.add(alias)
                    expanded.append(alias)
    return expanded


def campaign_sku_match(skus: list[str]):
    """SQL predicate: selected standing SKUs plus confirmed S4 Pain → V5 when V5 is in scope."""
    if not skus:
        return True
    normalized = expand_campaign_skus(skus)
    wants_v5 = "Master V5" in normalized
    wants_s4 = "Master S4" in {normalize_product_code(code) for code in normalized}
    stored = CustomerIntelligence.recommended_product.in_(normalized)
    confirmed = confirmed_s4_pain_v5_clause()
    if wants_v5:
        return or_(stored, confirmed)
    if wants_s4:
        return and_(stored, ~confirmed)
    return stored


def _as_upload_uuid(upload_id) -> uuid.UUID | None:
    if upload_id is None or upload_id == "":
        return None
    if isinstance(upload_id, uuid.UUID):
        return upload_id
    return uuid.UUID(str(upload_id))


def load_live_coverage_groups(db: Session, upload_id=None) -> list[dict]:
    """Distinct live (product, PP, segment) groups with conservative Coverage assignment."""
    uid = _as_upload_uuid(upload_id)
    pp = purchase_power_category_expr()
    q = (
        db.query(
            CustomerIntelligence.recommended_product,
            pp.label("pp_category"),
            CustomerIntelligence.ceragem_segment,
            func.count(Customer.customer_id),
        )
        .join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
        .filter(CustomerIntelligence.recommended_product.isnot(None))
        .group_by(CustomerIntelligence.recommended_product, pp, CustomerIntelligence.ceragem_segment)
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)

    groups: list[dict] = []
    for product, pp_category, segment, count in q.all():
        assignment = assign_conservative_coverage(
            str(product or ""),
            purchase_power_category=str(pp_category or "Medium"),
            ceragem_segment=str(segment).strip() if segment else None,
        )
        groups.append(
            {
                "product": str(product or ""),
                "pp_category": str(pp_category or "Medium"),
                "segment": str(segment).strip() if segment else None,
                "customers": int(count or 0),
                "outreach": assignment.outreach_sku,
                "bucket": assignment.bucket,
            }
        )
    return groups


def _group_clause(group: dict):
    pp = purchase_power_category_expr()
    parts = [
        CustomerIntelligence.recommended_product == group["product"],
        pp == group["pp_category"],
    ]
    segment = group.get("segment")
    if segment:
        parts.append(CustomerIntelligence.ceragem_segment == segment)
    else:
        parts.append(
            or_(
                CustomerIntelligence.ceragem_segment.is_(None),
                CustomerIntelligence.ceragem_segment == "",
            )
        )
    return and_(*parts)


def promo_reach_match(skus: list[str], groups: list[dict]):
    wanted = {normalize_product_code(code) for code in expand_campaign_skus(skus)}
    clauses = [
        _group_clause(group)
        for group in groups
        if group.get("outreach") and normalize_product_code(str(group["outreach"])) in wanted
    ]
    if not clauses:
        return literal(False)
    return or_(*clauses)


def promo_reach_display_expr(skus: list[str], groups: list[dict]):
    wanted = {normalize_product_code(code) for code in expand_campaign_skus(skus)}
    whens = [
        (_group_clause(group), literal(normalize_product_code(str(group["outreach"]))))
        for group in groups
        if group.get("outreach") and normalize_product_code(str(group["outreach"])) in wanted
    ]
    if not whens:
        return CustomerIntelligence.recommended_product
    return case(*whens, else_=CustomerIntelligence.recommended_product)


def apply_campaign_skus(
    q,
    skus: list[str],
    *,
    audience_mode: str | None = None,
    db: Session | None = None,
    upload_id=None,
    coverage_groups: list[dict] | None = None,
):
    if not skus:
        return q
    mode = normalize_audience_mode(audience_mode)
    if mode != AUDIENCE_MODE_PROMO_REACH:
        return q.filter(campaign_sku_match(skus))
    groups = coverage_groups
    if groups is None:
        if db is None:
            raise ValueError("db is required for promo_reach audience mode")
        groups = load_live_coverage_groups(db, upload_id)
    return q.filter(promo_reach_match(skus, groups))


def persist_confirmed_s4_pain_v5_targets(db: Session) -> int:
    """Rewrite stored recommended_product for the confirmed S4 Pain → V5 pocket."""
    result = db.execute(
        update(CustomerIntelligence)
        .where(confirmed_s4_pain_v5_clause())
        .values(recommended_product="Master V5")
    )
    db.commit()
    return int(result.rowcount or 0)
