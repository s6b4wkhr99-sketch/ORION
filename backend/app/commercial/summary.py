"""Commercial Intelligence dashboard aggregates for Mission Control."""

from __future__ import annotations

import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.campaign.standing_promo_demand import (
    build_standing_promo_opportunity_rows,
    merge_standing_promo_product_rows,
    pick_highest_conversion_opportunity,
)
from app.intelligence.promo_price_response import (
    aggregate_conservative_promo_coverage,
    load_promo_coverage_cohort_rows,
)
from app.commercial.catalog import active_products, get_runtime_version, product_by_code
from app.commercial.engine import build_commercial_kpis, default_promotion_amount
from app.commercial.promotion_policy import (
    active_promotion_order,
    build_active_promotion_rows,
    is_promotion_active,
    promo_code,
    promotion_pct,
    standing_promo_product_order,
)
from app.models.customer import Customer, CustomerIntelligence
from app.reference.registry import COMMERCIAL_VERSION, PRODUCT_CATALOG


def build_active_promotions() -> list[dict]:
    return build_active_promotion_rows()


def _sku_highlight(row: dict | None) -> dict | None:
    if not row:
        return None
    product = row.get("product")
    standing_margin_pct = None
    if product and is_promotion_active(product):
        standing_margin_pct = promotion_pct(product)
    return {
        "product": product,
        "net_profit_pct": row.get("net_profit_pct"),
        "net_profit": row.get("net_profit"),
        "recommended_promotion": row.get("recommended_promotion"),
        "promotion_pct": row.get("promotion_pct"),
        "promo_code": row.get("promo_code"),
        "standing_promotion": bool(row.get("promo_code")),
        "standing_promotion_margin_pct": standing_margin_pct,
    }


def _standing_promo_kpi_rows() -> list[dict]:
    """KPI rows for standing promo SKUs — independent of published catalog completeness."""
    rows: list[dict] = []
    for code in standing_promo_product_order():
        promo = default_promotion_amount(code)
        rows.append({"product": code, **build_commercial_kpis(code, promo)})
    return rows


def build_best_standing_promo_sku(anchor_margin_pct: float | None = None) -> dict | None:
    """Standing promo SKU whose net margin is closest to the non-promo anchor (e.g. V9 vs V6)."""
    rows = _standing_promo_kpi_rows()
    if not rows:
        return None
    if anchor_margin_pct is not None:
        best = min(
            rows,
            key=lambda row: abs(float(row.get("net_profit_pct") or 0) - float(anchor_margin_pct)),
        )
    else:
        best = max(rows, key=lambda row: float(row.get("net_profit_pct") or -999))
    return _sku_highlight(best)


def _standing_promo_rows(catalog_rows: list[dict]) -> list[dict]:
    active = set(standing_promo_product_order())
    return [row for row in catalog_rows if row.get("product") in active]


def _catalog_kpis() -> list[dict]:
    rows: list[dict] = []
    for product in active_products():
        code = product["code"]
        promo = default_promotion_amount(code)
        kpis = build_commercial_kpis(code, promo)
        rows.append({"product": code, **kpis})
    return rows


def _intelligence_customer_count(db: Session, upload_id: uuid.UUID | None) -> int:
    """Full scoped customer count with intelligence — Promotion Coverage DB denominator."""
    try:
        q = db.query(func.count(Customer.customer_id)).join(
            CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id
        )
        if upload_id:
            q = q.filter(Customer.upload_id == upload_id)
        value = q.scalar()
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 0
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _promotion_coverage(
    db: Session,
    upload_id: uuid.UUID | None,
    product_rows: list[dict],
    targetable_customers: float = 0,
) -> list[dict]:
    """Conservative reach per standing-promo SKU — afford-own gate; M10 adds segment-in."""
    product_rows = merge_standing_promo_product_rows(product_rows)
    product_map = {row.get("product"): row for row in product_rows if row.get("product")}
    db_total = _intelligence_customer_count(db, upload_id)
    if db_total <= 0 and targetable_customers:
        db_total = int(targetable_customers)
    if db_total <= 0:
        total_product_customers = sum(int(row.get("customers") or 0) for row in product_rows)
        db_total = max(total_product_customers, 0)

    denominator = max(db_total, 1)
    cohort_rows = load_promo_coverage_cohort_rows(db, upload_id)
    responsive_by_sku: dict[str, dict] = {}
    unassigned: dict[str, int] = {"customers": 0, "afford_own": 0, "unreachable": 0}
    if cohort_rows:
        responsive_by_sku, unassigned = aggregate_conservative_promo_coverage(cohort_rows)
    responsive_basis = bool(responsive_by_sku or unassigned.get("customers"))

    coverage: list[dict] = []
    for product_code in standing_promo_product_order():
        code = promo_code(product_code)
        if not code:
            continue
        row = product_map.get(product_code)
        primary_direct = int(row.get("customers") or 0) if row else 0
        responsive = responsive_by_sku.get(product_code, {})
        direct_count = int(responsive.get("direct") or 0) if responsive_basis else primary_direct
        reach = int(responsive.get("customers") or 0) if responsive_basis else primary_direct
        if responsive_basis:
            kpi_basis = "conservative_promo_reach"
        else:
            kpi_basis = "primary_sku_direct"

        coverage.append(
            {
                "product": product_code,
                "promo_code": code,
                "customers": reach,
                "coverage_pct": round(reach / denominator * 100, 1),
                "projected": False,
                "primary_direct": primary_direct,
                "direct": direct_count,
                "up_convert": int(responsive.get("up_convert") or 0),
                "down_convert": int(responsive.get("down_convert") or 0),
                "segment_in": int(responsive.get("segment_in") or 0),
                "kpi_basis": kpi_basis,
            }
        )

    unassigned_customers = int(unassigned.get("customers") or 0)
    if unassigned_customers > 0:
        coverage.append(
            {
                "product": None,
                "promo_code": "—",
                "customers": unassigned_customers,
                "coverage_pct": round(unassigned_customers / denominator * 100, 1),
                "projected": False,
                "afford_own": int(unassigned.get("afford_own") or 0),
                "unreachable": int(unassigned.get("unreachable") or 0),
                "kpi_basis": "conservative_unassigned",
            }
        )

    return coverage


def build_promotion_coverage_snapshot(
    db: Session,
    upload_id: uuid.UUID | str | None = None,
) -> dict:
    """Live conservative Promotion Coverage — not wrapped in executive dashboard cache."""
    uid: uuid.UUID | None = None
    if upload_id:
        uid = upload_id if isinstance(upload_id, uuid.UUID) else uuid.UUID(str(upload_id))
    cohort_rows = load_promo_coverage_cohort_rows(db, uid)
    product_counts: dict[str, int] = {}
    for row in cohort_rows:
        code = str(row.get("product") or "").strip()
        if not code:
            continue
        product_counts[code] = product_counts.get(code, 0) + int(row.get("customers") or 0)
    product_rows = [
        {"product": product, "customers": customers, "revenue": 0.0, "share_pct": 0.0}
        for product, customers in sorted(product_counts.items(), key=lambda item: -item[1])
    ]
    targetable = float(_intelligence_customer_count(db, uid))
    coverage = _promotion_coverage(
        db,
        uid,
        product_rows,
        targetable_customers=targetable,
    )
    return {
        "promotion_coverage_version": "conservative-v1",
        "promotion_coverage": coverage,
        "db_customers": int(targetable or sum(product_counts.values())),
    }


def _commercial_health_score(catalog_rows: list[dict], product_rows: list[dict]) -> float:
    if not catalog_rows:
        return 0.0

    margin_scores = [float(r.get("net_profit_pct") or 0) for r in catalog_rows]
    avg_margin = sum(margin_scores) / len(margin_scores)
    margin_component = min(40.0, max(0.0, avg_margin * 100))

    complete = sum(
        1
        for p in active_products()
        if p.get("selling_price") is not None and float(p.get("selling_price") or 0) > 0
    )
    catalog_component = (complete / max(len(active_products()), 1)) * 20.0

    normalized_rows = merge_standing_promo_product_rows(product_rows)
    total_customers = sum(int(r.get("customers") or 0) for r in normalized_rows) or 1
    with_promo = 0
    for row in normalized_rows:
        product = row.get("product")
        if product and is_promotion_active(product):
            with_promo += int(row.get("customers") or 0)
    coverage_component = (with_promo / total_customers) * 25.0

    compliance_component = 25.0
    return round(min(100.0, margin_component + catalog_component + coverage_component + compliance_component), 1)


def build_commercial_intelligence_summary(
    db: Session,
    upload_id: uuid.UUID | None,
    product_rows: list[dict],
    expected_revenue: float,
    expected_orders: float,
    le_frame_incentive: float,
    targetable_customers: float = 0,
    segment_rows: list[dict] | None = None,
    pp_bands: dict[str, float] | None = None,
) -> dict:
    product_rows = merge_standing_promo_product_rows(product_rows)
    catalog_rows = _catalog_kpis()
    version = get_runtime_version() or COMMERCIAL_VERSION

    active_promotions = build_active_promotions()

    active_codes = set(active_promotion_order())
    non_standing_rows = [row for row in catalog_rows if row.get("product") not in active_codes]
    by_margin = sorted(catalog_rows, key=lambda r: float(r.get("net_profit_pct") or 0), reverse=True)
    by_non_standing_profit = sorted(
        non_standing_rows,
        key=lambda r: float(r.get("net_profit") or 0),
        reverse=True,
    )
    by_profit = sorted(catalog_rows, key=lambda r: float(r.get("net_profit") or 0), reverse=True)
    standing_rows = _standing_promo_kpi_rows()
    by_promoted_margin = sorted(standing_rows, key=lambda r: float(r.get("net_profit_pct") or 0), reverse=True)
    by_promoted_profit = sorted(standing_rows, key=lambda r: float(r.get("net_profit") or 0), reverse=True)

    highest_margin = by_non_standing_profit[0] if by_non_standing_profit else (by_margin[0] if by_margin else None)
    highest_profit = by_profit[0] if by_profit else None
    best_promoted = by_promoted_margin[0] if by_promoted_margin else None
    best_promoted_profit = by_promoted_profit[0] if by_promoted_profit else None
    segments = segment_rows or []
    purchase_power = pp_bands or {"high": 0.0, "medium": 0.0, "low": 100.0}
    highest_opportunity = pick_highest_conversion_opportunity(
        db,
        upload_id,
        product_rows,
        segments,
        purchase_power,
        targetable_customers=targetable_customers,
    )
    if not highest_opportunity:
        standing_opportunity_rows = build_standing_promo_opportunity_rows(db, upload_id, product_rows)
        highest_opportunity = standing_opportunity_rows[0] if standing_opportunity_rows else None
        if not highest_opportunity:
            by_revenue = sorted(product_rows, key=lambda r: float(r.get("revenue") or 0), reverse=True)
            highest_opportunity = by_revenue[0] if by_revenue else None
    opportunity_customers = int(highest_opportunity.get("customers") or 0) if highest_opportunity else 0
    customer_share_pct = (
        highest_opportunity.get("customer_share_pct")
        if highest_opportunity and highest_opportunity.get("customer_share_pct") is not None
        else None
    )
    if customer_share_pct is None and highest_opportunity:
        total_product_customers = sum(int(row.get("customers") or 0) for row in product_rows)
        customer_denominator = max(targetable_customers or total_product_customers, 1)
        customer_share_pct = round(opportunity_customers / customer_denominator * 100, 1)

    anchor_margin = float(highest_margin.get("net_profit_pct") or 0) if highest_margin else None
    best_standing_promo = build_best_standing_promo_sku(anchor_margin) or _sku_highlight(best_promoted)

    return {
        "commercial_version": version,
        "pricing_version": version,
        "kpi_basis": "standing_promotion_policy",
        "active_promotions": active_promotions,
        "promotion_coverage": _promotion_coverage(
            db, upload_id, product_rows, targetable_customers=targetable_customers
        ),
        "promotion_coverage_version": "conservative-v1",
        "promo_policy_version": "2026.07-promo-policy-v2",
        "commercial_health_score": _commercial_health_score(catalog_rows, product_rows),
        "highest_margin_sku": _sku_highlight(highest_margin),
        "highest_profit_sku": _sku_highlight(highest_profit),
        "best_standing_promo_sku": best_standing_promo,
        "best_standing_promo_profit_sku": _sku_highlight(best_promoted_profit),
        "highest_opportunity_sku": {
            "product": highest_opportunity["product"] if highest_opportunity else None,
            "expected_revenue": highest_opportunity.get("revenue") or highest_opportunity.get("conversion_weighted_revenue") if highest_opportunity else None,
            "customers": opportunity_customers if highest_opportunity else None,
            "customer_share_pct": customer_share_pct,
            "revenue_share_pct": highest_opportunity.get("share_pct") if highest_opportunity else None,
            "share_pct": highest_opportunity.get("share_pct") if highest_opportunity else None,
            "projected": bool(highest_opportunity.get("projected")) if highest_opportunity else False,
            "segment_fit": highest_opportunity.get("segment_fit") if highest_opportunity else None,
            "pp_accessibility": highest_opportunity.get("pp_accessibility") if highest_opportunity else None,
            "weighted_conversion": highest_opportunity.get("weighted_conversion") if highest_opportunity else None,
            "kpi_basis": highest_opportunity.get("kpi_basis") if highest_opportunity else None,
        },
        "expected_le_frame_revenue": round(le_frame_incentive, 2),
        "expected_revenue": round(expected_revenue, 2),
        "expected_conversion_orders": round(expected_orders, 2),
        "sku_commercial_kpis": catalog_rows,
    }
