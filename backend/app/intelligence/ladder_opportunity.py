"""Ladder-addressable product opportunity — promo-aware ladder pick per cohort.

Uses Rule-065 ladder resolution with market nudges and standing promos applied at
state / metro / ZIP level. Sleep and price-resistance layers are skipped for dashboard
performance. Standing-promo outreach credit rolls donor SKUs into promo legend targets.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

from sqlalchemy import case, func, literal
from sqlalchemy.orm import Session

from app.mapping.standardization import standardize_zip
from app.geo.zip_economics import PREMIUM_INCOME_THRESHOLD, MID_INCOME_LOWER_BOUND
from app.intelligence.recommendation_rules import RecommendationInputs, resolve_rule_065_product
from app.models.customer import Customer, CustomerIntelligence
from app.models.zip import ZipIntelligence
from app.reference.registry import SUPPORTED_PRODUCTS

GeoDimension = Literal["city", "zip", "state"]


def _index_level_expr(column):
    return case(
        (column >= 0.75, literal("High")),
        (column >= 0.45, literal("Medium")),
        else_=literal("Low"),
    )


def _geo_expr(dimension: GeoDimension):
    if dimension == "city":
        return func.coalesce(Customer.city, literal("Unknown"))
    if dimension == "zip":
        return Customer.zip
    return Customer.state


def _normalize_geo(dimension: GeoDimension, value: str | None) -> str | None:
    if value is None:
        return None
    if dimension == "zip":
        return standardize_zip(str(value).strip()) or str(value).strip()
    return str(value)


def _income_tier_expr():
    return case(
        (ZipIntelligence.top50_rank.is_(True), literal("High")),
        (ZipIntelligence.median_income >= PREMIUM_INCOME_THRESHOLD, literal("High")),
        (ZipIntelligence.median_income >= MID_INCOME_LOWER_BOUND, literal("Mid")),
        (ZipIntelligence.median_income.isnot(None), literal("Lower")),
        else_=literal("Unknown"),
    )


def _resolve_promo_aware_ladder_product(
    *,
    ceragem,
    prizm,
    pain_cat,
    pp_cat,
    ls_cat,
    premium_zip,
    zip_income_tier,
    customer_state,
) -> str | None:
    """Promo + market nudge SKU from Rule-065 (no sleep / resistance)."""
    inputs = RecommendationInputs(
        ceragem_segment=str(ceragem or "Mid-Low+ · Wellness"),
        prizm_segment=str(prizm or "Unknown"),
        purchase_power_category=str(pp_cat or "Low"),
        pain_index_category=str(pain_cat or "Low"),
        lifestyle_category=str(ls_cat or "Low"),
        message_direction="Product Education Message",
        email_response_index=0.0,
        premium_zip=bool(premium_zip),
        customer_state=customer_state,
        zip_income_tier=str(zip_income_tier or "Unknown"),
    )
    result = resolve_rule_065_product(inputs, apply_sleep=False, apply_resistance=False)
    return result.get("recommended_product")


def _fetch_segment_cohort_rows(
    db: Session,
    upload_id,
    state: str | None,
    dimension: GeoDimension,
    *,
    state_filter: list[str] | None = None,
):
    pain_level = _index_level_expr(CustomerIntelligence.pain_index)
    pp_level = _index_level_expr(CustomerIntelligence.purchase_power_index)
    lifestyle_level = _index_level_expr(CustomerIntelligence.lifestyle_index)
    income_tier = _income_tier_expr()
    geo = _geo_expr(dimension)

    q = (
        db.query(
            geo,
            CustomerIntelligence.ceragem_segment,
            CustomerIntelligence.prizm_proxy_segment,
            pain_level,
            pp_level,
            lifestyle_level,
            income_tier,
            ZipIntelligence.top50_rank,
            Customer.state,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_conversion),
            func.sum(CustomerIntelligence.expected_revenue),
            func.avg(CustomerIntelligence.purchase_power_index),
            func.avg(CustomerIntelligence.campaign_priority),
            func.avg(CustomerIntelligence.pain_index),
            func.avg(CustomerIntelligence.lifestyle_index),
        )
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .outerjoin(ZipIntelligence, ZipIntelligence.zip == Customer.zip)
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    if state:
        q = q.filter(Customer.state == state)
    elif state_filter:
        q = q.filter(Customer.state.in_(state_filter))

    return q.group_by(
        geo,
        CustomerIntelligence.ceragem_segment,
        CustomerIntelligence.prizm_proxy_segment,
        pain_level,
        pp_level,
        lifestyle_level,
        income_tier,
        ZipIntelligence.top50_rank,
        Customer.state,
    ).all()


def _credit_cohort_to_product(
    buckets: dict[tuple[str, str], dict],
    *,
    geo: str,
    product: str,
    customers: int,
    cohort_orders: float,
    cohort_revenue: float,
    avg_pp,
    avg_cp,
    avg_pain,
    avg_life,
) -> None:
    key = (geo, product)
    bucket = buckets[key]
    bucket["customers"] += customers
    bucket["orders"] = round(float(bucket["orders"]) + cohort_orders, 2)
    bucket["revenue"] = round(float(bucket["revenue"]) + cohort_revenue, 2)
    if avg_pp is not None:
        bucket["pp_values"].append(float(avg_pp))
    if avg_cp is not None:
        bucket["cp_values"].append(float(avg_cp))
    if avg_pain is not None:
        bucket["pain_weighted"] += float(avg_pain) * customers
    if avg_life is not None:
        bucket["lifestyle_weighted"] += float(avg_life) * customers


def _expand_cohort_rows_to_geo_product(
    rows,
    dimension: GeoDimension,
) -> dict[tuple[str, str], dict]:
    buckets: dict[tuple[str, str], dict] = defaultdict(
        lambda: {
            "customers": 0,
            "orders": 0.0,
            "revenue": 0.0,
            "pp_values": [],
            "cp_values": [],
            "pain_weighted": 0.0,
            "lifestyle_weighted": 0.0,
        },
    )

    for (
        geo_raw,
        ceragem,
        prizm,
        pain_cat,
        pp_cat,
        ls_cat,
        zip_income_tier,
        top50_rank,
        customer_state,
        count,
        orders,
        revenue,
        avg_pp,
        avg_cp,
        avg_pain,
        avg_life,
    ) in rows:
        geo = _normalize_geo(dimension, geo_raw)
        if not geo:
            continue
        customers = int(count or 0)
        if customers <= 0:
            continue

        product = _resolve_promo_aware_ladder_product(
            ceragem=ceragem,
            prizm=prizm,
            pain_cat=pain_cat,
            pp_cat=pp_cat,
            ls_cat=ls_cat,
            premium_zip=bool(top50_rank),
            zip_income_tier=zip_income_tier,
            customer_state=customer_state,
        )
        if not product:
            continue

        _credit_cohort_to_product(
            buckets,
            geo=geo,
            product=product,
            customers=customers,
            cohort_orders=float(orders or 0),
            cohort_revenue=float(revenue or 0),
            avg_pp=avg_pp,
            avg_cp=avg_cp,
            avg_pain=avg_pain,
            avg_life=avg_life,
        )

    return dict(buckets)


def aggregate_ladder_geo_product_opportunity(
    db: Session,
    upload_id,
    state: str | None,
    dimension: GeoDimension,
    *,
    state_filter: list[str] | None = None,
) -> dict[tuple[str, str], dict]:
    rows = _fetch_segment_cohort_rows(
        db,
        upload_id,
        state,
        dimension,
        state_filter=state_filter,
    )
    return _expand_cohort_rows_to_geo_product(rows, dimension)


def aggregate_ladder_addressable_opportunity(
    db: Session,
    upload_id,
    state: str | None,
) -> dict[str, dict[str, float | int]]:
    """Per-product totals for a state (or national when state is None)."""
    if state:
        rows = aggregate_ladder_geo_product_opportunity(db, upload_id, state, "state")
        totals: dict[str, dict[str, float | int]] = defaultdict(
            lambda: {"customers": 0, "orders": 0.0, "revenue": 0.0},
        )
        for (_geo, product), bucket in rows.items():
            totals[product]["customers"] += int(bucket["customers"])
            totals[product]["orders"] = round(float(totals[product]["orders"]) + float(bucket["orders"]), 2)
            totals[product]["revenue"] = round(float(totals[product]["revenue"]) + float(bucket["revenue"]), 2)
        return dict(totals)

    rows = _fetch_segment_cohort_rows(db, upload_id, None, "state")
    totals = defaultdict(lambda: {"customers": 0, "orders": 0.0, "revenue": 0.0})
    for (
        _geo,
        ceragem,
        prizm,
        pain_cat,
        pp_cat,
        ls_cat,
        zip_income_tier,
        top50_rank,
        customer_state,
        count,
        orders,
        revenue,
    ) in rows:
        customers = int(count or 0)
        if customers <= 0:
            continue
        product = _resolve_promo_aware_ladder_product(
            ceragem=ceragem,
            prizm=prizm,
            pain_cat=pain_cat,
            pp_cat=pp_cat,
            ls_cat=ls_cat,
            premium_zip=bool(top50_rank),
            zip_income_tier=zip_income_tier,
            customer_state=customer_state,
        )
        if not product:
            continue
        cohort_orders = float(orders or 0)
        cohort_revenue = float(revenue or 0)
        bucket = totals[product]
        bucket["customers"] += customers
        bucket["orders"] = round(float(bucket["orders"]) + cohort_orders, 2)
        bucket["revenue"] = round(float(bucket["revenue"]) + cohort_revenue, 2)

    return dict(totals)


def aggregate_ladder_state_product_rows(
    db: Session,
    upload_id,
    state_codes: list[str],
) -> list[dict]:
    """State × product rows for Opportunity Radar."""
    geo_rows = aggregate_ladder_geo_product_opportunity(
        db,
        upload_id,
        None,
        "state",
        state_filter=state_codes,
    )
    out: list[dict] = []
    for (state, product), bucket in geo_rows.items():
        if state not in state_codes:
            continue
        customers = int(bucket["customers"])
        if customers <= 0:
            continue
        out.append(
            {
                "state": state,
                "product": product,
                "customers": customers,
                "orders": float(bucket["orders"]),
                "revenue": float(bucket["revenue"]),
            }
        )
    return out


def merge_primary_and_ladder_opportunity(
    primary_rows: list[dict],
    ladder_totals: dict[str, dict[str, float | int]],
) -> list[dict]:
    """Combine primary SKU counts with promo-aware ladder floor + outreach credit."""
    primary_by_product = {row["product"]: row for row in primary_rows}
    out: list[dict] = []

    for product in SUPPORTED_PRODUCTS:
        primary = primary_by_product.get(product, {})
        ladder = ladder_totals.get(product, {})
        customers = max(
            int(primary.get("expected_customers") or 0),
            int(ladder.get("customers") or 0),
        )
        revenue = max(
            float(primary.get("expected_revenue") or 0),
            float(ladder.get("revenue") or 0),
        )
        orders = max(
            float(primary.get("expected_orders") or 0),
            float(ladder.get("orders") or 0),
        )
        out.append(
            {
                "product": product,
                "expected_customers": customers,
                "expected_orders": round(orders, 2),
                "expected_revenue": round(revenue, 2),
            }
        )
    return out


def merge_geo_product_buckets(
    primary: dict[tuple[str, str], dict],
    ladder: dict[tuple[str, str], dict],
) -> dict[tuple[str, str], dict]:
    """Merge primary geo×product buckets with promo-aware ladder addressable floor."""
    merged: dict[tuple[str, str], dict] = {}
    for key in set(primary) | set(ladder):
        p = primary.get(key, {})
        l = ladder.get(key, {})
        customers = max(int(p.get("customers") or 0), int(l.get("customers") or 0))
        if customers <= 0:
            continue
        pp_values = p.get("pp_values") or l.get("pp_values") or []
        cp_values = p.get("cp_values") or l.get("cp_values") or []
        merged[key] = {
            "customers": customers,
            "orders": max(float(p.get("orders") or 0), float(l.get("orders") or 0)),
            "revenue": max(float(p.get("revenue") or 0), float(l.get("revenue") or 0)),
            "pp_values": pp_values,
            "cp_values": cp_values,
            "pain_weighted": max(float(p.get("pain_weighted") or 0), float(l.get("pain_weighted") or 0)),
            "lifestyle_weighted": max(
                float(p.get("lifestyle_weighted") or 0),
                float(l.get("lifestyle_weighted") or 0),
            ),
        }
    return merged


def merge_state_product_cells(
    primary_rows: list[dict],
    ladder_rows: list[dict],
) -> dict[tuple[str, str], dict]:
    cells: dict[tuple[str, str], dict] = {}
    for row in primary_rows:
        key = (row["state"], row["product"])
        cells[key] = dict(row)
    for row in ladder_rows:
        key = (row["state"], row["product"])
        existing = cells.get(key, {"state": row["state"], "product": row["product"], "customers": 0, "orders": 0.0, "revenue": 0.0})
        cells[key] = {
            "state": row["state"],
            "product": row["product"],
            "customers": max(int(existing.get("customers") or 0), int(row["customers"])),
            "orders": max(float(existing.get("orders") or 0), float(row["orders"])),
            "revenue": max(float(existing.get("revenue") or 0), float(row["revenue"])),
        }
    return cells


def merge_zip_product_scores(
    primary: dict[str, dict[str, dict]],
    ladder: dict[tuple[str, str], dict],
) -> dict[str, dict[str, dict]]:
    merged: dict[str, dict[str, dict]] = defaultdict(dict)
    for zip_code, products in primary.items():
        for product, metrics in products.items():
            merged[zip_code][product] = dict(metrics)

    for (zip_code, product), bucket in ladder.items():
        existing = merged[zip_code].get(product, {"expected_revenue": 0.0, "target_customers": 0})
        merged[zip_code][product] = {
            "expected_revenue": round(
                max(float(existing.get("expected_revenue") or 0), float(bucket["revenue"])),
                2,
            ),
            "target_customers": max(
                int(existing.get("target_customers") or 0),
                int(bucket["customers"]),
            ),
        }
    return {zip_code: dict(products) for zip_code, products in merged.items()}
