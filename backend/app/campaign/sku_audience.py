"""Campaign SKU audience — Opportunity Finder / export use the same product-fit rule as Coverage."""

from __future__ import annotations

from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session

from app.models.customer import CustomerIntelligence
from app.reference.registry import normalize_product_code

S4_PRODUCT_ALIASES = ("Master S4", "Pause S4", "Master V4")
LOW_PP_INDEX_MAX = 0.34
CAMPAIGN_SKU_FILTER_VERSION = "v5-s4-pain-confirmed-v1"


def confirmed_s4_pain_v5_clause():
    """S4 + Pain + Low PP → confirmed FDA V5 campaign target (same pocket as Coverage)."""
    return and_(
        CustomerIntelligence.recommended_product.in_(S4_PRODUCT_ALIASES),
        CustomerIntelligence.ceragem_segment.ilike("%Pain%"),
        CustomerIntelligence.purchase_power_index.isnot(None),
        CustomerIntelligence.purchase_power_index < LOW_PP_INDEX_MAX,
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


def apply_campaign_skus(q, skus: list[str]):
    if not skus:
        return q
    return q.filter(campaign_sku_match(skus))


def persist_confirmed_s4_pain_v5_targets(db: Session) -> int:
    """Rewrite stored recommended_product for the confirmed S4 Pain → V5 pocket."""
    result = db.execute(
        update(CustomerIntelligence)
        .where(confirmed_s4_pain_v5_clause())
        .values(recommended_product="Master V5")
    )
    db.commit()
    return int(result.rowcount or 0)
