"""State, ZIP, Product, ROI, and Export preview analytics."""

import uuid
from collections import Counter, defaultdict

from sqlalchemy import case, func, literal
from sqlalchemy.orm import Session, defer

from app.intelligence.forecasting import le_frame_incentive
from app.reference.registry import SUPPORTED_PRODUCTS
from app.reference.service import get_reference_version
from app.acquisition.rollup import has_upload_rollup
from app.cache.dashboard_cache import DASHBOARD_BUILD_VERSION, cached_dashboard
from app.models.campaign import Campaign, CampaignProduct, CampaignState
from app.models.customer import Customer, CustomerIntelligence
from app.models.export import ExportJob, ExportTemplate
from app.models.raw import RawUpload
from app.models.scale import UploadRollup
from app.market.market_intelligence import (
    _bands_weighted_score,
    enrich_state_dashboard,
    get_metro_dashboard,
)
from app.models.zip import ZipIntelligence
from app.campaign.opportunity_score import (
    compute_state_opportunity_score,
    compute_zip_opportunity_score,
)

PRODUCTS = list(SUPPORTED_PRODUCTS)
ZIP_OPPORTUNITY_DEFAULT = 50
ZIP_OPPORTUNITY_ALLOWED = (0, 50, 100, 250, 500)
ZIP_OPPORTUNITY_LIMIT = ZIP_OPPORTUNITY_DEFAULT
CITY_REVENUE_LIMIT = 25
CITY_PER_PRODUCT_LIMIT = 25
CITY_ZIP_POOL_LIMIT = 2500
ZIP_CUSTOMER_PREVIEW_LIMIT = 100


def _normalize_zip_limit(limit: int | None) -> int:
    if limit is None:
        return ZIP_OPPORTUNITY_DEFAULT
    if limit == 0:
        return 0
    return limit if limit in ZIP_OPPORTUNITY_ALLOWED else ZIP_OPPORTUNITY_DEFAULT


def _parse_upload_id(upload_id: str | uuid.UUID | None):
    if not upload_id:
        return None
    if isinstance(upload_id, uuid.UUID):
        return upload_id
    return uuid.UUID(upload_id)


def _index_level(value: float | None) -> str:
    if value is None:
        return "Low"
    if value >= 0.75:
        return "High"
    if value >= 0.45:
        return "Medium"
    return "Low"


def _index_score(value: float | None) -> float:
    """Map normalized intelligence index (0–1) to a 0–100 chart score."""
    if value is None:
        return 0.0
    return round(float(value) * 100, 1)


def _enrich_zip_rows_with_geo_indices(
    db: Session,
    rows: list[dict],
    *,
    state: str | None = None,
    upload_id: str | None = None,
) -> list[dict]:
    """Attach average pain/lifestyle indices per ZIP for city-level geo charts."""
    zips = [str(row.get("zip")) for row in rows if row.get("zip") and row.get("zip") != "Unknown"]
    if not zips:
        return rows

    uid = _parse_upload_id(upload_id)
    q = (
        db.query(
            Customer.zip,
            func.avg(CustomerIntelligence.pain_index),
            func.avg(CustomerIntelligence.lifestyle_index),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(Customer.zip.in_(zips))
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    if state:
        q = q.filter(Customer.state == state)

    scores = {
        str(zip_code): {
            "pain_index": float(pain) if pain is not None else None,
            "lifestyle_index": float(lifestyle) if lifestyle is not None else None,
        }
        for zip_code, pain, lifestyle in q.group_by(Customer.zip).all()
    }

    enriched: list[dict] = []
    for row in rows:
        patch = scores.get(str(row.get("zip")), {})
        enriched.append({**row, **patch})
    return enriched


def _index_level_expr(column):
    return case(
        (column >= 0.75, literal("High")),
        (column >= 0.45, literal("Medium")),
        else_=literal("Low"),
    )


def _scoped_intel_join(db: Session, upload_id: str | None = None, state: str | None = None):
    """Base join for aggregate queries — never loads full customer rows."""
    uid = _parse_upload_id(upload_id)
    q = (
        db.query(Customer, CustomerIntelligence)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .options(
            defer(CustomerIntelligence.trace_json),
            defer(CustomerIntelligence.framework_json),
        )
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    if state:
        q = q.filter(Customer.state == state)
    return q


def _state_stats_query(db: Session, upload_id: str | None = None):
    uid = _parse_upload_id(upload_id)
    q = (
        db.query(
            Customer.state,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_conversion),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    return q.group_by(Customer.state)


def _segment_distribution_sql(
    db: Session,
    upload_id: str | None,
    state: str | None,
    zip_code: str | None = None,
) -> dict:
    uid = _parse_upload_id(upload_id)

    def grouped_counts(column):
        q = (
            db.query(column, func.count(Customer.customer_id))
            .select_from(Customer)
            .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        )
        if uid:
            q = q.filter(Customer.upload_id == uid)
        if state:
            q = q.filter(Customer.state == state)
        if zip_code:
            q = q.filter(Customer.zip == zip_code)
        return dict(q.group_by(column).all())

    def grouped_index_counts(column):
        level = _index_level_expr(column)
        q = (
            db.query(level, func.count(Customer.customer_id))
            .select_from(Customer)
            .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        )
        if uid:
            q = q.filter(Customer.upload_id == uid)
        if state:
            q = q.filter(Customer.state == state)
        if zip_code:
            q = q.filter(Customer.zip == zip_code)
        return {str(k or "Low"): int(v) for k, v in q.group_by(level).all()}

    return {
        "prizm": {str(k or "Unknown"): int(v) for k, v in grouped_counts(CustomerIntelligence.prizm_proxy_segment).items()},
        "ceragem": {str(k or "Unknown"): int(v) for k, v in grouped_counts(CustomerIntelligence.ceragem_segment).items()},
        "purchase_power": grouped_index_counts(CustomerIntelligence.purchase_power_index),
        "pain_index": grouped_index_counts(CustomerIntelligence.pain_index),
        "lifestyle": grouped_index_counts(CustomerIntelligence.lifestyle_index),
        "brand_familiarity": grouped_index_counts(CustomerIntelligence.brand_familiarity_index),
    }


def _product_opportunity_sql(db: Session, upload_id: str | None, state: str | None) -> list[dict]:
    from app.intelligence.ladder_opportunity import (
        aggregate_ladder_addressable_opportunity,
        merge_primary_and_ladder_opportunity,
    )

    uid = _parse_upload_id(upload_id)
    q = (
        db.query(
            CustomerIntelligence.recommended_product,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_conversion),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    if state:
        q = q.filter(Customer.state == state)
    stats = {
        str(product or "Unknown"): {
            "customers": int(count or 0),
            "orders": float(orders or 0),
            "revenue": float(revenue or 0),
        }
        for product, count, orders, revenue in q.group_by(CustomerIntelligence.recommended_product).all()
    }
    primary_rows = [
        {
            "product": p,
            "expected_customers": stats.get(p, {}).get("customers", 0),
            "expected_orders": round(stats.get(p, {}).get("orders", 0), 2),
            "expected_revenue": round(stats.get(p, {}).get("revenue", 0), 2),
        }
        for p in PRODUCTS
    ]
    ladder_totals = aggregate_ladder_addressable_opportunity(db, uid, state)
    return merge_primary_and_ladder_opportunity(primary_rows, ladder_totals)


def _zip_opportunity_sql(db: Session, upload_id: str | None, state: str | None, limit: int = ZIP_OPPORTUNITY_LIMIT) -> list[dict]:
    uid = _parse_upload_id(upload_id)
    q = (
        db.query(
            Customer.zip,
            func.max(Customer.city),
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_revenue),
            func.avg(CustomerIntelligence.purchase_power_index),
            func.avg(CustomerIntelligence.campaign_priority),
            func.avg(CustomerIntelligence.pain_index),
            func.avg(CustomerIntelligence.lifestyle_index),
            func.max(CustomerIntelligence.recommended_product),
        )
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    if state:
        q = q.filter(Customer.state == state)
    rows = (
        q.group_by(Customer.zip)
        .order_by(func.sum(CustomerIntelligence.expected_revenue).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "zip": zip_code or "Unknown",
            "city": city or "—",
            "target_customers": int(count or 0),
            "purchase_power": _index_level(float(avg_pp) if avg_pp is not None else None),
            "recommended_product": product,
            "expected_revenue": round(float(revenue or 0), 2),
            "campaign_priority": _index_level(float(avg_cp) if avg_cp is not None else None),
            "pain_index": float(avg_pain) if avg_pain is not None else None,
            "lifestyle_index": float(avg_life) if avg_life is not None else None,
        }
        for zip_code, city, count, revenue, avg_pp, avg_cp, avg_pain, avg_life, product in rows
    ]


def _score_city_row(row: dict, *, max_revenue: float) -> dict:
    customers = int(row.get("customers") or 0)
    orders = float(row.get("orders") or 0)
    revenue = float(row.get("revenue") or 0)
    conversion = orders / customers if customers else 0.0
    avg_pp = row.get("avg_purchase_power")
    avg_cp = row.get("avg_campaign_priority")
    opportunity_score = compute_zip_opportunity_score(
        {
            "revenue": revenue,
            "conversion": conversion,
            "purchase_power": row.get("purchase_power") or _index_level(avg_pp),
            "campaign_priority": row.get("campaign_priority") or _index_level(avg_cp),
            "purchase_power_index_score": round(float(avg_pp or 0) * 100, 1),
            "recommended_product": row.get("top_product"),
        },
        max_revenue=max_revenue,
    )
    product = row.get("product") or row.get("top_product")
    return {
        "city": row["city"],
        "revenue": round(revenue, 2),
        "customers": customers,
        "orders": round(orders, 2),
        "conversion": round(conversion, 6),
        "opportunity_score": opportunity_score,
        "product": product,
        "top_product": product,
        "purchase_power": row.get("purchase_power") or _index_level(avg_pp),
        "campaign_priority": row.get("campaign_priority") or _index_level(avg_cp),
        "pain_index_score": _index_score(row.get("avg_pain_index")),
        "lifestyle_index_score": _index_score(row.get("avg_lifestyle_index")),
    }


def _finalize_city_opportunity_by_product(
    buckets: dict[str, list[dict]],
    *,
    limit: int = CITY_PER_PRODUCT_LIMIT,
) -> dict[str, list[dict]]:
    from app.campaign.standing_promo_demand import pad_geo_product_rows

    out: dict[str, list[dict]] = {}
    for product in PRODUCTS:
        ranked = sorted(buckets.get(product, []), key=lambda row: -float(row.get("revenue") or 0))
        ranked = pad_geo_product_rows(product, ranked, buckets, geo_field="city", limit=limit)
        if not ranked:
            continue
        max_revenue = max(float(row.get("revenue") or 0) for row in ranked) or 1.0
        out[product] = [
            _score_city_row({**row, "product": product, "top_product": product}, max_revenue=max_revenue)
            for row in ranked[:limit]
        ]
    return out


def _city_opportunity_by_product_from_zips(
    zip_rows: list[dict],
    limit: int = CITY_PER_PRODUCT_LIMIT,
) -> dict[str, list[dict]]:
    agg: dict[tuple[str, str], dict] = defaultdict(
        lambda: {
            "revenue": 0.0,
            "customers": 0,
            "orders": 0.0,
            "pp_values": [],
            "cp_values": [],
            "pain_weighted": 0.0,
            "lifestyle_weighted": 0.0,
        }
    )
    for row in zip_rows:
        product = row.get("recommended_product")
        if not product:
            continue
        city = row.get("city") or "Unknown"
        bucket = agg[(str(product), city)]
        bucket["city"] = city
        customers = int(row.get("target_customers") or 0)
        bucket["revenue"] += float(row.get("expected_revenue") or 0)
        bucket["customers"] += customers
        bucket["orders"] += float(row.get("expected_orders") or row.get("target_customers", 0) * 0.03)
        pp = row.get("purchase_power")
        if pp:
            bucket["pp_values"].append({"High": 0.75, "Medium": 0.55, "Low": 0.25}.get(pp, 0.45))
        cp = row.get("campaign_priority")
        if cp:
            bucket["cp_values"].append({"High": 0.75, "Medium": 0.55, "Low": 0.25}.get(cp, 0.45))
        pain = row.get("pain_index")
        if pain is not None and customers:
            bucket["pain_weighted"] += float(pain) * customers
        lifestyle = row.get("lifestyle_index")
        if lifestyle is not None and customers:
            bucket["lifestyle_weighted"] += float(lifestyle) * customers

    by_product: dict[str, list[dict]] = defaultdict(list)
    for (product, _city), bucket in agg.items():
        avg_pp = sum(bucket["pp_values"]) / len(bucket["pp_values"]) if bucket["pp_values"] else None
        avg_cp = sum(bucket["cp_values"]) / len(bucket["cp_values"]) if bucket["cp_values"] else None
        customers = bucket["customers"]
        avg_pain = bucket["pain_weighted"] / customers if customers and bucket["pain_weighted"] else None
        avg_lifestyle = bucket["lifestyle_weighted"] / customers if customers and bucket["lifestyle_weighted"] else None
        by_product[product].append(
            {
                "city": bucket["city"],
                "revenue": bucket["revenue"],
                "customers": customers,
                "orders": bucket["orders"],
                "avg_purchase_power": avg_pp,
                "avg_campaign_priority": avg_cp,
                "avg_pain_index": avg_pain,
                "avg_lifestyle_index": avg_lifestyle,
            }
        )

    return _finalize_city_opportunity_by_product(by_product, limit=limit)


def _city_opportunity_by_product_sql(
    db: Session,
    upload_id: str | None,
    state: str | None,
    limit: int = CITY_PER_PRODUCT_LIMIT,
) -> dict[str, list[dict]]:
    from app.intelligence.ladder_opportunity import (
        aggregate_ladder_geo_product_opportunity,
        merge_geo_product_buckets,
    )

    uid = _parse_upload_id(upload_id)
    city_expr = func.coalesce(Customer.city, literal("Unknown"))
    q = (
        db.query(
            city_expr,
            CustomerIntelligence.recommended_product,
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
        .filter(CustomerIntelligence.recommended_product.isnot(None))
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    if state:
        q = q.filter(Customer.state == state)

    primary_buckets: dict[tuple[str, str], dict] = {}
    for city, product, count, orders, revenue, avg_pp, avg_cp, avg_pain, avg_life in q.group_by(
        city_expr, CustomerIntelligence.recommended_product
    ).all():
        if not product:
            continue
        customers = int(count or 0)
        primary_buckets[(str(city), str(product))] = {
            "customers": customers,
            "orders": float(orders or 0),
            "revenue": float(revenue or 0),
            "pp_values": [float(avg_pp)] if avg_pp is not None else [],
            "cp_values": [float(avg_cp)] if avg_cp is not None else [],
            "pain_weighted": float(avg_pain or 0) * customers,
            "lifestyle_weighted": float(avg_life or 0) * customers,
        }

    ladder_buckets = aggregate_ladder_geo_product_opportunity(db, uid, state, "city")
    merged = merge_geo_product_buckets(primary_buckets, ladder_buckets)

    by_product: dict[str, list[dict]] = defaultdict(list)
    for (city, product), bucket in merged.items():
        customers = int(bucket["customers"])
        pp_values = bucket.get("pp_values") or []
        cp_values = bucket.get("cp_values") or []
        by_product[str(product)].append(
            {
                "city": city,
                "revenue": float(bucket["revenue"]),
                "customers": customers,
                "orders": float(bucket["orders"]),
                "avg_purchase_power": (sum(pp_values) / len(pp_values)) if pp_values else None,
                "avg_campaign_priority": (sum(cp_values) / len(cp_values)) if cp_values else None,
                "avg_pain_index": (float(bucket["pain_weighted"]) / customers) if customers else None,
                "avg_lifestyle_index": (float(bucket["lifestyle_weighted"]) / customers) if customers else None,
            }
        )

    return _finalize_city_opportunity_by_product(by_product, limit=limit)


def _city_opportunity_from_zips(zip_rows: list[dict], limit: int = CITY_REVENUE_LIMIT) -> list[dict]:
    agg: dict[str, dict] = defaultdict(
        lambda: {
            "revenue": 0.0,
            "customers": 0,
            "orders": 0.0,
            "pp_values": [],
            "cp_values": [],
            "products": Counter(),
        }
    )
    for row in zip_rows:
        city = row.get("city") or "Unknown"
        bucket = agg[city]
        bucket["revenue"] += float(row.get("expected_revenue") or 0)
        bucket["customers"] += int(row.get("target_customers") or 0)
        bucket["orders"] += float(row.get("expected_orders") or row.get("target_customers", 0) * 0.03)
        product = row.get("recommended_product")
        if product:
            bucket["products"][product] += int(row.get("target_customers") or 1)
        pp = row.get("purchase_power")
        if pp:
            bucket["pp_values"].append({"High": 0.75, "Medium": 0.55, "Low": 0.25}.get(pp, 0.45))
        cp = row.get("campaign_priority")
        if cp:
            bucket["cp_values"].append({"High": 0.75, "Medium": 0.55, "Low": 0.25}.get(cp, 0.45))

    if not agg:
        return []

    max_revenue = max(v["revenue"] for v in agg.values()) or 1.0
    ranked = sorted(agg.items(), key=lambda item: -item[1]["revenue"])[:limit]
    out: list[dict] = []
    for city, bucket in ranked:
        avg_pp = sum(bucket["pp_values"]) / len(bucket["pp_values"]) if bucket["pp_values"] else None
        avg_cp = sum(bucket["cp_values"]) / len(bucket["cp_values"]) if bucket["cp_values"] else None
        top_product = bucket["products"].most_common(1)[0][0] if bucket["products"] else None
        out.append(
            _score_city_row(
                {
                    "city": city,
                    "revenue": bucket["revenue"],
                    "customers": bucket["customers"],
                    "orders": bucket["orders"],
                    "avg_purchase_power": avg_pp,
                    "avg_campaign_priority": avg_cp,
                    "top_product": top_product,
                },
                max_revenue=max_revenue,
            )
        )
    return out


def _city_opportunity_sql(db: Session, upload_id: str | None, state: str | None, limit: int = CITY_REVENUE_LIMIT) -> list[dict]:
    uid = _parse_upload_id(upload_id)
    city_expr = func.coalesce(Customer.city, literal("Unknown"))
    q = (
        db.query(
            city_expr,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_conversion),
            func.sum(CustomerIntelligence.expected_revenue),
            func.avg(CustomerIntelligence.purchase_power_index),
            func.avg(CustomerIntelligence.campaign_priority),
        )
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    if state:
        q = q.filter(Customer.state == state)
    rows = (
        q.group_by(city_expr)
        .order_by(func.sum(CustomerIntelligence.expected_revenue).desc())
        .limit(limit)
        .all()
    )
    if not rows:
        return []

    cities = [str(city) for city, *_ in rows]
    product_q = (
        db.query(city_expr, CustomerIntelligence.recommended_product, func.count(Customer.customer_id))
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if uid:
        product_q = product_q.filter(Customer.upload_id == uid)
    if state:
        product_q = product_q.filter(Customer.state == state)
    product_q = product_q.filter(city_expr.in_(cities)).group_by(city_expr, CustomerIntelligence.recommended_product)
    top_product_by_city: dict[str, str] = {}
    product_counts: dict[str, Counter] = defaultdict(Counter)
    for city, product, count in product_q.all():
        if product:
            product_counts[str(city)][product] += int(count or 0)
    for city, counter in product_counts.items():
        if counter:
            top_product_by_city[city] = counter.most_common(1)[0][0]

    max_revenue = max(float(revenue or 0) for _, _, _, revenue, _, _ in rows) or 1.0
    out: list[dict] = []
    for city, count, orders, revenue, avg_pp, avg_cp in rows:
        out.append(
            _score_city_row(
                {
                    "city": str(city),
                    "revenue": float(revenue or 0),
                    "customers": int(count or 0),
                    "orders": float(orders or 0),
                    "avg_purchase_power": float(avg_pp) if avg_pp is not None else None,
                    "avg_campaign_priority": float(avg_cp) if avg_cp is not None else None,
                    "top_product": top_product_by_city.get(str(city)),
                },
                max_revenue=max_revenue,
            )
        )
    return out


def _revenue_by_city_sql(db: Session, upload_id: str | None, state: str | None, limit: int = CITY_REVENUE_LIMIT) -> list[dict]:
    return _city_opportunity_sql(db, upload_id, state, limit=limit)


def _state_dashboard_sql(db: Session, upload_id: str | None = None, state: str | None = None, zip_limit: int = ZIP_OPPORTUNITY_DEFAULT) -> dict:
    """Fast path: SQL aggregates only — safe for 645k+ / 2.5M rows."""
    state_rows = _state_stats_query(db, upload_id).all()
    state_stats = {
        (st or "Unknown"): {
            "count": int(count or 0),
            "orders": float(orders or 0),
            "revenue": float(revenue or 0),
        }
        for st, count, orders, revenue in state_rows
    }
    available_states = sorted(state_stats.keys())
    selected = state or (available_states[0] if len(available_states) == 1 else None)
    scope = selected or "Unknown"

    if selected:
        target = state_stats.get(scope, {}).get("count", 0)
        expected_orders = state_stats.get(scope, {}).get("orders", 0)
        expected_revenue = state_stats.get(scope, {}).get("revenue", 0)
    else:
        target = sum(v["count"] for v in state_stats.values())
        expected_orders = sum(v["orders"] for v in state_stats.values())
        expected_revenue = sum(v["revenue"] for v in state_stats.values())
    avg_conversion = expected_orders / target if target else 0

    campaign_rows = db.query(CampaignState)
    if selected:
        campaign_rows = campaign_rows.filter(CampaignState.state == selected)
    campaign_rows = campaign_rows.all()
    campaign_revenue = sum(r.revenue or 0 for r in campaign_rows)
    campaign_cost = sum(r.cost or 0 for r in campaign_rows)
    campaign_roi = round((campaign_revenue - campaign_cost) / campaign_cost, 4) if campaign_cost else None

    return {
        "selected_state": selected,
        "available_states": available_states,
        "kpis": {
            "target_customers": target,
            "expected_orders": round(expected_orders, 2),
            "expected_revenue": round(expected_revenue, 2),
            "average_conversion": round(avg_conversion, 4),
            "campaign_roi": campaign_roi,
            "le_frame_incentive": round(le_frame_incentive(expected_revenue), 2),
        },
        "state_heatmap": [
            {"state": st, "revenue": round(v["revenue"], 2), "count": v["count"]}
            for st, v in sorted(state_stats.items(), key=lambda x: -x[1]["revenue"])
        ],
        "revenue_by_city": _revenue_by_city_sql(db, upload_id, selected) if selected else [],
        "revenue_by_city_by_product": _city_opportunity_by_product_sql(db, upload_id, selected) if selected else {},
        "segment_distribution": _segment_distribution_sql(db, upload_id, selected),
        "zip_opportunity": _zip_opportunity_sql(db, upload_id, selected, limit=zip_limit) if zip_limit else [],
        "product_opportunity": _product_opportunity_sql(db, upload_id, selected),
        "campaign_history": _campaign_history(db, selected),
        "rollup_source": False,
        "aggregate_source": True,
    }


def _customer_query(
    db: Session,
    upload_id: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    product: str | None = None,
):
    q = db.query(Customer, CustomerIntelligence).join(
        CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id
    ).options(
        defer(CustomerIntelligence.trace_json),
        defer(CustomerIntelligence.framework_json),
    )
    uid = _parse_upload_id(upload_id)
    if uid:
        q = q.filter(Customer.upload_id == uid)
    if state:
        q = q.filter(Customer.state == state)
    if zip_code:
        q = q.filter(Customer.zip == zip_code)
    if product:
        q = q.filter(CustomerIntelligence.recommended_product == product)
    return q


def _campaign_history(db: Session, selected: str | None) -> list[dict]:
    history = []
    for camp in db.query(Campaign).order_by(Campaign.start_date.desc()).all():
        st_rows = [
            r for r in db.query(CampaignState).filter(CampaignState.campaign_id == camp.campaign_id).all()
            if not selected or r.state == selected
        ]
        if not st_rows and selected:
            continue
        rows = st_rows or db.query(CampaignState).filter(CampaignState.campaign_id == camp.campaign_id).all()
        rev = sum(r.revenue or 0 for r in rows)
        clicks = sum(r.click for r in rows)
        sent = sum(r.sent for r in rows)
        roi_vals = [r.roi for r in rows if r.roi is not None]
        history.append({
            "campaign_id": camp.campaign_id,
            "campaign": camp.campaign_name,
            "date": camp.start_date.isoformat() if camp.start_date else camp.created_at.isoformat(),
            "revenue": round(rev, 2),
            "roi": round(sum(roi_vals) / len(roi_vals), 4) if roi_vals else None,
            "ctr": round(clicks / sent, 4) if sent else None,
            "conversion": round(sum(r.conversion or 0 for r in rows), 4),
            "status": camp.status,
        })
    return history


def has_any_rollup(db: Session) -> bool:
    return db.query(UploadRollup.id).limit(1).first() is not None


def _rollup_counts_by_key(
    db: Session,
    dimension: str,
    state: str | None = None,
) -> dict[str, int]:
    q = (
        db.query(UploadRollup.key, func.sum(UploadRollup.customer_count))
        .filter(UploadRollup.dimension == dimension)
    )
    if state:
        q = q.filter(UploadRollup.scope == state)
    return {str(k or "Unknown"): int(v or 0) for k, v in q.group_by(UploadRollup.key).all()}


# Index-band dimensions map to the underlying intelligence column, used for the live
# fallback when a rollup predates that band dimension being written.
_INDEX_BAND_COLUMNS = {
    "purchase_power": CustomerIntelligence.purchase_power_index,
    "pain": CustomerIntelligence.pain_index,
    "lifestyle": CustomerIntelligence.lifestyle_index,
    "brand": CustomerIntelligence.brand_familiarity_index,
}


def _live_index_band_counts(
    db: Session,
    dimension: str,
    state: str | None = None,
    upload_id: uuid.UUID | None = None,
) -> dict[str, int]:
    """Compute High/Medium/Low band counts directly from customer intelligence."""
    column = _INDEX_BAND_COLUMNS.get(dimension)
    if column is None:
        return {}
    level = _index_level_expr(column)
    q = (
        db.query(level, func.count(Customer.customer_id))
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    if state:
        q = q.filter(Customer.state == state)
    return {str(k or "Low"): int(v) for k, v in q.group_by(level).all()}


def _index_counts_by_key(
    db: Session,
    dimension: str,
    state: str | None = None,
    upload_id: uuid.UUID | None = None,
) -> dict[str, int]:
    """Rollup band counts, self-healing to a live query when the rollup lacks this band.

    Older upload rollups were built before some index bands (e.g. brand_familiarity)
    were added to the rollup loop, so those states have no rollup rows for that band.
    """
    counts = _rollup_counts_by_key(db, dimension, state)
    if counts:
        return counts
    return _live_index_band_counts(db, dimension, state, upload_id)


def _rollup_product_stats(db: Session, state: str | None = None) -> dict[str, dict]:
    q = (
        db.query(
            UploadRollup.key,
            func.sum(UploadRollup.customer_count),
            func.sum(UploadRollup.expected_orders),
            func.sum(UploadRollup.expected_revenue),
        )
        .filter(UploadRollup.dimension == "product")
    )
    if state:
        q = q.filter(UploadRollup.scope == state)
    return {
        str(product or "Unknown"): {
            "customers": int(count or 0),
            "orders": float(orders or 0),
            "revenue": float(revenue or 0),
        }
        for product, count, orders, revenue in q.group_by(UploadRollup.key).all()
    }


def _rollup_zip_opportunity(db: Session, state: str | None = None, limit: int = ZIP_OPPORTUNITY_LIMIT) -> list[dict]:
    import json

    q = (
        db.query(
            UploadRollup.key,
            func.max(UploadRollup.scope),
            func.sum(UploadRollup.customer_count),
            func.sum(UploadRollup.expected_revenue),
        )
        .filter(UploadRollup.dimension == "zip")
    )
    if state:
        q = q.filter(UploadRollup.scope == state)
    rows = (
        q.group_by(UploadRollup.key)
        .order_by(func.sum(UploadRollup.expected_revenue).desc())
        .limit(limit)
        .all()
    )
    if not rows:
        return []

    zip_keys = [zip_code for zip_code, _, _, _ in rows]
    payload_by_zip: dict[str, dict] = {}
    for zip_code, payload_json in (
        db.query(UploadRollup.key, UploadRollup.payload_json)
        .filter(UploadRollup.dimension == "zip", UploadRollup.key.in_(zip_keys), UploadRollup.payload_json.isnot(None))
        .all()
    ):
        if zip_code and zip_code not in payload_by_zip and payload_json:
            try:
                payload_by_zip[zip_code] = json.loads(payload_json)
            except json.JSONDecodeError:
                payload_by_zip[zip_code] = {}

    out = []
    for zip_code, scope, count, revenue in rows:
        payload = payload_by_zip.get(zip_code or "", {})
        out.append(
            {
                "zip": zip_code or "Unknown",
                "city": payload.get("city") or "—",
                "target_customers": int(count or 0),
                "purchase_power": payload.get("purchase_power", "Low"),
                "recommended_product": payload.get("recommended_product"),
                "expected_revenue": round(float(revenue or 0), 2),
                "campaign_priority": payload.get("campaign_priority", "Low"),
            }
        )
    return _enrich_zip_rows_with_geo_indices(db, out, state=state)


def _rollup_city_revenue(db: Session, state: str | None = None, limit: int = CITY_REVENUE_LIMIT) -> list[dict]:
    return _city_opportunity_from_zips(_rollup_zip_opportunity(db, state, limit=500), limit=limit)


def _has_city_prod_rollup(db: Session, upload_id: uuid.UUID | str | None) -> bool:
    """True if the accurate per-(city, product) rollup exists for this scope."""
    q = db.query(UploadRollup.upload_id).filter(UploadRollup.dimension == "city_prod")
    uid = _parse_upload_id(upload_id)
    if uid:
        q = q.filter(UploadRollup.upload_id == uid)
    return q.first() is not None


def _rollup_city_by_product(
    db: Session,
    state: str | None = None,
    upload_id: str | None = None,
    limit: int = CITY_PER_PRODUCT_LIMIT,
) -> dict[str, list[dict]]:
    """Revenue-by-city-per-product from the city_prod rollup (100% of customers)."""
    import json

    q = db.query(UploadRollup).filter(UploadRollup.dimension == "city_prod")
    if state:
        q = q.filter(UploadRollup.scope == state)
    uid = _parse_upload_id(upload_id)
    if uid:
        q = q.filter(UploadRollup.upload_id == uid)

    agg: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"city": None, "revenue": 0.0, "customers": 0, "orders": 0.0, "pain": 0.0, "life": 0.0, "pp": 0.0, "cp": 0.0}
    )
    for row in q.all():
        payload = json.loads(row.payload_json) if row.payload_json else {}
        city = payload.get("city") or "Unknown"
        product = payload.get("product") or "Unknown"
        b = agg[(product, city)]
        b["city"] = city
        b["revenue"] += float(row.expected_revenue or 0)
        b["customers"] += int(row.customer_count or 0)
        b["orders"] += float(row.expected_orders or 0)
        b["pain"] += float(payload.get("pain_sum", 0) or 0)
        b["life"] += float(payload.get("lifestyle_sum", 0) or 0)
        b["pp"] += float(payload.get("pp_sum", 0) or 0)
        b["cp"] += float(payload.get("cp_sum", 0) or 0)

    by_product: dict[str, list[dict]] = defaultdict(list)
    for (product, _city), b in agg.items():
        c = b["customers"]
        by_product[product].append(
            {
                "city": b["city"],
                "revenue": b["revenue"],
                "customers": c,
                "orders": b["orders"],
                "avg_purchase_power": (b["pp"] / c) if c else None,
                "avg_campaign_priority": (b["cp"] / c) if c else None,
                "avg_pain_index": (b["pain"] / c) if c else None,
                "avg_lifestyle_index": (b["life"] / c) if c else None,
            }
        )

    if state:
        from app.intelligence.ladder_opportunity import (
            aggregate_ladder_geo_product_opportunity,
            merge_geo_product_buckets,
        )

        primary_buckets: dict[tuple[str, str], dict] = {}
        for (product, city), b in agg.items():
            customers = int(b["customers"])
            primary_buckets[(str(city), str(product))] = {
                "customers": customers,
                "orders": float(b["orders"]),
                "revenue": float(b["revenue"]),
                "pp_values": [(b["pp"] / customers)] if customers else [],
                "cp_values": [(b["cp"] / customers)] if customers else [],
                "pain_weighted": float(b["pain"]),
                "lifestyle_weighted": float(b["life"]),
            }
        ladder_buckets = aggregate_ladder_geo_product_opportunity(db, uid, state, "city")
        merged = merge_geo_product_buckets(primary_buckets, ladder_buckets)
        by_product = defaultdict(list)
        for (city, product), bucket in merged.items():
            customers = int(bucket["customers"])
            pp_values = bucket.get("pp_values") or []
            cp_values = bucket.get("cp_values") or []
            by_product[str(product)].append(
                {
                    "city": city,
                    "revenue": float(bucket["revenue"]),
                    "customers": customers,
                    "orders": float(bucket["orders"]),
                    "avg_purchase_power": (sum(pp_values) / len(pp_values)) if pp_values else None,
                    "avg_campaign_priority": (sum(cp_values) / len(cp_values)) if cp_values else None,
                    "avg_pain_index": (float(bucket["pain_weighted"]) / customers) if customers else None,
                    "avg_lifestyle_index": (float(bucket["lifestyle_weighted"]) / customers) if customers else None,
                }
            )

    return _finalize_city_opportunity_by_product(by_product, limit=limit)


def _rollup_city_revenue_from_cityprod(
    db: Session,
    state: str | None = None,
    upload_id: str | None = None,
    limit: int = CITY_REVENUE_LIMIT,
) -> list[dict]:
    """Top cities by revenue from the city_prod rollup (100% of customers)."""
    import json

    q = db.query(UploadRollup).filter(UploadRollup.dimension == "city_prod")
    if state:
        q = q.filter(UploadRollup.scope == state)
    uid = _parse_upload_id(upload_id)
    if uid:
        q = q.filter(UploadRollup.upload_id == uid)

    agg: dict[str, dict] = defaultdict(
        lambda: {"revenue": 0.0, "customers": 0, "orders": 0.0, "pp": 0.0, "cp": 0.0, "products": Counter()}
    )
    for row in q.all():
        payload = json.loads(row.payload_json) if row.payload_json else {}
        city = payload.get("city") or "Unknown"
        product = payload.get("product") or "Unknown"
        cust = int(row.customer_count or 0)
        b = agg[city]
        b["revenue"] += float(row.expected_revenue or 0)
        b["customers"] += cust
        b["orders"] += float(row.expected_orders or 0)
        b["pp"] += float(payload.get("pp_sum", 0) or 0)
        b["cp"] += float(payload.get("cp_sum", 0) or 0)
        b["products"][product] += cust

    if not agg:
        return []
    max_revenue = max(v["revenue"] for v in agg.values()) or 1.0
    ranked = sorted(agg.items(), key=lambda item: -item[1]["revenue"])[:limit]
    out: list[dict] = []
    for city, b in ranked:
        c = b["customers"]
        out.append(
            _score_city_row(
                {
                    "city": city,
                    "revenue": b["revenue"],
                    "customers": c,
                    "orders": b["orders"],
                    "avg_purchase_power": (b["pp"] / c) if c else None,
                    "avg_campaign_priority": (b["cp"] / c) if c else None,
                    "top_product": b["products"].most_common(1)[0][0] if b["products"] else None,
                },
                max_revenue=max_revenue,
            )
        )
    return out


def _state_dashboard_from_all_rollups(db: Session, state: str | None = None, zip_limit: int = ZIP_OPPORTUNITY_DEFAULT) -> dict:
    """Aggregate pre-computed upload_rollups across all batches — SQL only, no full-table scan."""
    state_rows = (
        db.query(
            UploadRollup.key,
            func.sum(UploadRollup.customer_count),
            func.sum(UploadRollup.expected_orders),
            func.sum(UploadRollup.expected_revenue),
        )
        .filter(UploadRollup.dimension == "state", UploadRollup.scope == "*")
        .group_by(UploadRollup.key)
        .all()
    )
    state_stats = {
        key: {
            "count": int(count or 0),
            "orders": float(orders or 0),
            "revenue": float(revenue or 0),
        }
        for key, count, orders, revenue in state_rows
    }
    available_states = sorted(state_stats.keys())
    selected = state or (available_states[0] if len(available_states) == 1 else None)
    scope = selected or "Unknown"

    if selected:
        target = state_stats.get(scope, {}).get("count", 0)
        expected_orders = state_stats.get(scope, {}).get("orders", 0)
        expected_revenue = state_stats.get(scope, {}).get("revenue", 0)
    else:
        target = sum(v["count"] for v in state_stats.values())
        expected_orders = sum(v["orders"] for v in state_stats.values())
        expected_revenue = sum(v["revenue"] for v in state_stats.values())
    avg_conversion = expected_orders / target if target else 0

    campaign_rows = db.query(CampaignState)
    if selected:
        campaign_rows = campaign_rows.filter(CampaignState.state == selected)
    campaign_rows = campaign_rows.all()
    campaign_revenue = sum(r.revenue or 0 for r in campaign_rows)
    campaign_cost = sum(r.cost or 0 for r in campaign_rows)
    campaign_roi = round((campaign_revenue - campaign_cost) / campaign_cost, 4) if campaign_cost else None

    product_stats = _rollup_product_stats(db, selected)
    zip_opportunity = _rollup_zip_opportunity(db, selected, limit=zip_limit) if zip_limit else []
    # Aggregate cities from the city_prod rollup so the national view reflects 100% of revenue
    # (the previous top-N ZIP pool only captured ~60%), without a full-table customer scan.
    revenue_by_city = _rollup_city_revenue_from_cityprod(db, selected, limit=CITY_REVENUE_LIMIT) if selected else []
    revenue_by_city_by_product = _rollup_city_by_product(db, selected) if selected else {}

    return {
        "selected_state": selected,
        "available_states": available_states,
        "kpis": {
            "target_customers": target,
            "expected_orders": round(expected_orders, 2),
            "expected_revenue": round(expected_revenue, 2),
            "average_conversion": round(avg_conversion, 4),
            "campaign_roi": campaign_roi,
            "le_frame_incentive": round(le_frame_incentive(expected_revenue), 2),
        },
        "state_heatmap": [
            {"state": st, "revenue": round(v["revenue"], 2), "count": v["count"]}
            for st, v in sorted(state_stats.items(), key=lambda x: -x[1]["revenue"])
        ],
        "revenue_by_city": revenue_by_city,
        "revenue_by_city_by_product": revenue_by_city_by_product,
        "segment_distribution": {
            "prizm": _rollup_counts_by_key(db, "prizm", selected),
            "ceragem": _rollup_counts_by_key(db, "ceragem", selected),
            "purchase_power": _index_counts_by_key(db, "purchase_power", selected),
            "pain_index": _index_counts_by_key(db, "pain", selected),
            "lifestyle": _index_counts_by_key(db, "lifestyle", selected),
            "brand_familiarity": _index_counts_by_key(db, "brand", selected),
        },
        "zip_opportunity": zip_opportunity,
        "product_opportunity": [
            {
                "product": p,
                "expected_customers": product_stats.get(p, {}).get("customers", 0),
                "expected_orders": round(product_stats.get(p, {}).get("orders", 0), 2),
                "expected_revenue": round(product_stats.get(p, {}).get("revenue", 0), 2),
            }
            for p in PRODUCTS
        ],
        "campaign_history": _campaign_history(db, selected),
        "rollup_source": True,
        "global_rollup": True,
    }


def _state_dashboard_from_rollup(db: Session, upload_id: uuid.UUID, state: str | None = None, zip_limit: int = ZIP_OPPORTUNITY_DEFAULT) -> dict:
    import json

    state_rows = (
        db.query(UploadRollup)
        .filter(UploadRollup.upload_id == upload_id, UploadRollup.dimension == "state", UploadRollup.scope == "*")
        .all()
    )
    state_stats = {
        row.key: {"count": row.customer_count, "orders": row.expected_orders, "revenue": row.expected_revenue}
        for row in state_rows
    }
    available_states = sorted(state_stats.keys())
    selected = state or (available_states[0] if len(available_states) == 1 else None)
    scope = selected or "Unknown"

    target = state_stats.get(scope, {}).get("count", 0) if selected else sum(v["count"] for v in state_stats.values())
    expected_orders = state_stats.get(scope, {}).get("orders", 0) if selected else sum(v["orders"] for v in state_stats.values())
    expected_revenue = state_stats.get(scope, {}).get("revenue", 0) if selected else sum(v["revenue"] for v in state_stats.values())
    avg_conversion = expected_orders / target if target else 0

    campaign_rows = db.query(CampaignState)
    if selected:
        campaign_rows = campaign_rows.filter(CampaignState.state == selected)
    campaign_rows = campaign_rows.all()
    campaign_revenue = sum(r.revenue or 0 for r in campaign_rows)
    campaign_cost = sum(r.cost or 0 for r in campaign_rows)
    campaign_roi = round((campaign_revenue - campaign_cost) / campaign_cost, 4) if campaign_cost else None

    prizm_dist = Counter()
    ceragem_dist = Counter()
    pp_dist = Counter()
    pain_dist = Counter()
    lifestyle_dist = Counter()
    brand_dist = Counter()
    product_stats: dict[str, dict] = defaultdict(lambda: {"customers": 0, "orders": 0.0, "revenue": 0.0})
    zip_agg: dict[str, dict] = {}

    for row in db.query(UploadRollup).filter(UploadRollup.upload_id == upload_id).all():
        if selected and row.scope not in ("*", scope) and row.dimension != "state":
            if row.scope != scope:
                continue
        if row.dimension == "prizm" and (not selected or row.scope == scope):
            prizm_dist[row.key] += row.customer_count
        elif row.dimension == "ceragem" and (not selected or row.scope == scope):
            ceragem_dist[row.key] += row.customer_count
        elif row.dimension == "purchase_power" and (not selected or row.scope == scope):
            pp_dist[row.key] += row.customer_count
        elif row.dimension == "pain" and (not selected or row.scope == scope):
            pain_dist[row.key] += row.customer_count
        elif row.dimension == "lifestyle" and (not selected or row.scope == scope):
            lifestyle_dist[row.key] += row.customer_count
        elif row.dimension == "brand" and (not selected or row.scope == scope):
            brand_dist[row.key] += row.customer_count
        elif row.dimension == "product" and (not selected or row.scope == scope):
            product_stats[row.key]["customers"] += row.customer_count
            product_stats[row.key]["orders"] += row.expected_orders
            product_stats[row.key]["revenue"] += row.expected_revenue
        elif row.dimension == "zip" and (not selected or row.scope == scope):
            payload = {}
            if row.payload_json:
                try:
                    payload = json.loads(row.payload_json)
                except json.JSONDecodeError:
                    payload = {}
            city = payload.get("city") or "Unknown"
            zip_agg[row.key] = {
                "zip": row.key,
                "city": city,
                "target_customers": row.customer_count,
                "purchase_power": payload.get("purchase_power", "Low"),
                "recommended_product": payload.get("recommended_product"),
                "expected_revenue": round(row.expected_revenue, 2),
                "campaign_priority": payload.get("campaign_priority", "Low"),
            }

    # Revenue-by-city: prefer the per-(city, product) rollup (100% of customers, one product per
    # customer). The legacy zip-based fallback attributes an entire ZIP to its single dominant
    # product, which severely undercounts products that are rarely the ZIP-level pick (e.g. a
    # product recommended to many customers but never the top ZIP recommendation), so it is only
    # used for older uploads that predate the city_prod rollup.
    if selected and _has_city_prod_rollup(db, upload_id):
        revenue_by_city = _rollup_city_revenue_from_cityprod(
            db, selected, str(upload_id), limit=CITY_REVENUE_LIMIT
        )
        revenue_by_city_by_product = _rollup_city_by_product(db, selected, str(upload_id))
    elif selected:
        zip_rows = _enrich_zip_rows_with_geo_indices(
            db,
            sorted(zip_agg.values(), key=lambda x: -x["expected_revenue"]),
            state=selected,
            upload_id=str(upload_id),
        )
        revenue_by_city = _city_opportunity_from_zips(zip_rows, limit=CITY_REVENUE_LIMIT)
        revenue_by_city_by_product = _city_opportunity_by_product_from_zips(zip_rows)
    else:
        revenue_by_city = []
        revenue_by_city_by_product = {}
    return {
        "selected_state": selected,
        "available_states": available_states,
        "kpis": {
            "target_customers": target,
            "expected_orders": round(expected_orders, 2),
            "expected_revenue": round(expected_revenue, 2),
            "average_conversion": round(avg_conversion, 4),
            "campaign_roi": campaign_roi,
            "le_frame_incentive": round(le_frame_incentive(expected_revenue), 2),
        },
        "state_heatmap": [
            {"state": st, "revenue": round(v["revenue"], 2), "count": v["count"]}
            for st, v in sorted(state_stats.items(), key=lambda x: -x[1]["revenue"])
        ],
        "revenue_by_city": revenue_by_city,
        "revenue_by_city_by_product": revenue_by_city_by_product,
        "segment_distribution": {
            "prizm": dict(prizm_dist),
            "ceragem": dict(ceragem_dist),
            "purchase_power": dict(pp_dist) or _live_index_band_counts(db, "purchase_power", selected, upload_id),
            "pain_index": dict(pain_dist) or _live_index_band_counts(db, "pain", selected, upload_id),
            "lifestyle": dict(lifestyle_dist) or _live_index_band_counts(db, "lifestyle", selected, upload_id),
            "brand_familiarity": dict(brand_dist) or _live_index_band_counts(db, "brand", selected, upload_id),
        },
        "zip_opportunity": sorted(zip_agg.values(), key=lambda x: -x["expected_revenue"])[:zip_limit] if zip_limit else [],
        "product_opportunity": [
            {
                "product": p,
                "expected_customers": product_stats.get(p, {}).get("customers", 0),
                "expected_orders": round(product_stats.get(p, {}).get("orders", 0), 2),
                "expected_revenue": round(product_stats.get(p, {}).get("revenue", 0), 2),
            }
            for p in PRODUCTS
        ],
        "campaign_history": _campaign_history(db, selected),
        "rollup_source": True,
    }


def get_state_dashboard(
    db: Session,
    upload_id: str | None = None,
    state: str | None = None,
    zip_limit: int | None = None,
    *,
    lite: bool = False,
) -> dict:
    limit = _normalize_zip_limit(zip_limit)
    scope = f"{DASHBOARD_BUILD_VERSION}:{upload_id or 'all'}:{state or 'all'}:{limit}:{'lite' if lite else 'full'}"
    payload = cached_dashboard("state", scope, lambda: _get_state_dashboard(db, upload_id, state, limit))
    if lite or not payload.get("selected_state"):
        return payload
    return enrich_state_dashboard(db, payload, upload_id)


def get_metro_intelligence_dashboard(
    db: Session,
    upload_id: str | None = None,
    cbsa: str | None = None,
) -> dict:
    # Cache the heavy full-metro computation independently of the selected CBSA so that
    # switching between metros reuses a single cached payload instead of recomputing all 30.
    scope = f"{DASHBOARD_BUILD_VERSION}:{upload_id or 'all'}"
    payload = cached_dashboard("metro", scope, lambda: get_metro_dashboard(db, upload_id, None))
    if cbsa:
        selected = next((m for m in payload.get("metros", []) if m.get("cbsa_code") == cbsa), None)
        payload = {**payload, "selected_metro": selected}
    return payload


def _get_state_dashboard(
    db: Session,
    upload_id: str | None = None,
    state: str | None = None,
    zip_limit: int = ZIP_OPPORTUNITY_DEFAULT,
) -> dict:
    uid = _parse_upload_id(upload_id)
    if uid and has_upload_rollup(db, uid):
        payload = _state_dashboard_from_rollup(db, uid, state, zip_limit=zip_limit)
    elif uid is None and has_any_rollup(db):
        payload = _state_dashboard_from_all_rollups(db, state, zip_limit=zip_limit)
    else:
        payload = _state_dashboard_sql(db, upload_id, state, zip_limit=zip_limit)
    _attach_state_opportunity_score(payload)
    return payload


def _attach_state_opportunity_score(payload: dict) -> None:
    """Attach a self-contained opportunity_score (8-99) to the base state payload.

    This mirrors the metro opportunity blend (intelligence axes derived from segment bands +
    revenue share + conversion + product fit) using only data already present in the base
    payload, so the State View KPI card always shows a value — including in lite mode where
    enrich_state_dashboard (expensive geo bundle) is skipped.
    """
    kpis = payload.get("kpis") or {}
    customers = int(kpis.get("target_customers") or 0)
    if customers <= 0:
        payload["opportunity_score"] = 0.0
        return

    sd = payload.get("segment_distribution") or {}
    revenue = float(kpis.get("expected_revenue") or 0)
    # National scope revenue (sum) exceeds any single state, so max() yields a share of 1.0;
    # per-state scope compares against the strongest state for a proportional 0-1 share.
    max_state_rev = max(
        (float(s.get("revenue") or 0) for s in (payload.get("state_heatmap") or [])),
        default=revenue,
    )
    payload["opportunity_score"] = compute_state_opportunity_score(
        {
            "conversion": float(kpis.get("average_conversion") or 0),
            "revenue": revenue,
            "pain_index_score": _bands_weighted_score(sd.get("pain_index")),
            "purchase_power_score": _bands_weighted_score(sd.get("purchase_power")),
            "lifestyle_score": _bands_weighted_score(sd.get("lifestyle")),
            "brand_score": _bands_weighted_score(sd.get("brand_familiarity")),
            "digital_score": 45.0,
        },
        max_revenue=max(max_state_rev, revenue, 1.0),
    )


def _rollup_available_zips(db: Session, upload_id: uuid.UUID | None = None, limit: int = 100) -> list[str]:
    q = (
        db.query(
            UploadRollup.key,
            func.sum(UploadRollup.expected_revenue),
        )
        .filter(UploadRollup.dimension == "zip")
    )
    if upload_id:
        q = q.filter(UploadRollup.upload_id == upload_id)
    rows = (
        q.group_by(UploadRollup.key)
        .order_by(func.sum(UploadRollup.expected_revenue).desc())
        .limit(limit)
        .all()
    )
    return sorted([zip_code for zip_code, _ in rows if zip_code])


def _zip_rollup_summary(db: Session, upload_id: uuid.UUID | None, zip_code: str) -> dict:
    import json

    q = db.query(UploadRollup).filter(UploadRollup.dimension == "zip", UploadRollup.key == zip_code)
    if upload_id:
        q = q.filter(UploadRollup.upload_id == upload_id)
    rows = q.all()
    if not rows:
        return {}

    target_customers = sum(r.customer_count or 0 for r in rows)
    expected_revenue = sum(r.expected_revenue or 0 for r in rows)
    expected_orders = sum(r.expected_orders or 0 for r in rows)
    scope = rows[0].scope or "Unknown"
    payload = {}
    for row in rows:
        if row.payload_json:
            try:
                payload = json.loads(row.payload_json)
                break
            except json.JSONDecodeError:
                continue
    return {
        "state": scope,
        "target_customers": int(target_customers),
        "expected_orders": float(expected_orders),
        "expected_revenue": round(float(expected_revenue), 2),
        "campaign_priority": payload.get("campaign_priority", "Low"),
        "city": payload.get("city"),
        "purchase_power": payload.get("purchase_power", "Low"),
        "recommended_product": payload.get("recommended_product"),
    }


def _zip_sellable_products(db: Session, uid: uuid.UUID | None, zip_code: str | None) -> list[dict]:
    """Recommended-product mix for a ZIP — direct intelligence SKU counts only."""
    if not zip_code:
        return []
    q = (
        db.query(
            CustomerIntelligence.recommended_product,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_revenue),
            func.sum(CustomerIntelligence.expected_conversion),
        )
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(Customer.zip == zip_code, CustomerIntelligence.recommended_product.isnot(None))
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    rows = q.group_by(CustomerIntelligence.recommended_product).all()
    products = [
        {
            "product": str(product),
            "expected_customers": int(count or 0),
            "expected_revenue": round(float(revenue or 0), 2),
            "expected_orders": round(float(orders or 0), 2),
        }
        for product, count, revenue, orders in rows
    ]
    return sorted(products, key=lambda x: -x["expected_revenue"])


def _zip_dashboard_from_rollup(db: Session, upload_id: uuid.UUID | None, zip_code: str | None) -> dict:
    available_zips = _rollup_available_zips(db, upload_id, limit=100)
    selected = zip_code if zip_code in available_zips else (zip_code or (available_zips[0] if available_zips else None))
    summary_data = _zip_rollup_summary(db, upload_id, selected) if selected else {}
    ref = db.query(ZipIntelligence).filter(ZipIntelligence.zip == selected).first() if selected else None
    seg = _segment_distribution_sql(
        db,
        str(upload_id) if upload_id else None,
        summary_data.get("state"),
        zip_code=selected,
    ) if selected else {"prizm": {}, "ceragem": {}, "purchase_power": {}, "pain_index": {}, "lifestyle": {}}

    customer_rows = (
        _customer_query(db, str(upload_id) if upload_id else None, zip_code=selected)
        .limit(ZIP_CUSTOMER_PREVIEW_LIMIT)
        .all()
        if selected
        else []
    )
    target_customers = summary_data.get("target_customers") or len(customer_rows)
    expected_revenue = summary_data.get("expected_revenue") or sum(i.expected_revenue or 0 for _, i in customer_rows)
    priority = summary_data.get("campaign_priority") or "Low"

    return {
        "selected_zip": selected,
        "available_zips": available_zips,
        "summary": {
            "zip": selected,
            "city": (ref.city if ref and ref.city else None) or summary_data.get("city") or (customer_rows[0][0].city if customer_rows else "—"),
            "state": (ref.state if ref and ref.state else None) or summary_data.get("state") or (customer_rows[0][0].state if customer_rows else "—"),
            "median_income": ref.median_income if ref else None,
            "target_customers": target_customers,
            "expected_revenue": round(float(expected_revenue), 2),
            "campaign_priority": priority,
        },
        "income_intelligence": {
            "median_income": ref.median_income if ref else None,
            "top_50_income_zip": ref.top50_rank if ref else False,
            "population": ref.population if ref else None,
            "county": ref.county if ref else None,
            "reference_source": "zip_intelligence",
        },
        "sellable_products": _zip_sellable_products(db, upload_id, selected),
        "customer_intelligence": {
            "prizm_distribution": seg["prizm"],
            "ceragem_distribution": seg["ceragem"],
            "pain_index": seg["pain_index"],
            "lifestyle": seg["lifestyle"],
            "purchase_power": seg["purchase_power"],
        },
        "campaign_opportunity": [
            {"type": "Premium Opportunity", "score": seg["purchase_power"].get("High", 0), "label": "High purchase power households"},
            {"type": "Wellness Opportunity", "score": seg["ceragem"].get("High + Wellness", 0) + seg["ceragem"].get("Mid-High + Wellness", 0), "label": "Wellness-oriented segments"},
            {"type": "Pain Opportunity", "score": seg["pain_index"].get("High", 0), "label": "High pain index customers"},
            {"type": "Consultation Opportunity", "score": target_customers, "label": "Total targetable customers"},
        ],
        "customers": [
            {
                "id": str(c.customer_id),
                "email": c.email,
                "prizm_proxy_segment": i.prizm_proxy_segment,
                "ceragem_segment": i.ceragem_segment,
                "purchase_power": _index_level(i.purchase_power_index),
                "recommended_product": i.recommended_product,
                "campaign_priority": _index_level(i.campaign_priority),
                "expected_revenue": round(i.expected_revenue or 0, 2),
            }
            for c, i in customer_rows
        ],
        "rollup_source": True,
    }


def _zip_dashboard_sql(db: Session, upload_id: str | None = None, zip_code: str | None = None) -> dict:
    uid = _parse_upload_id(upload_id)
    zip_q = db.query(Customer.zip, func.count(Customer.customer_id))
    if uid:
        zip_q = zip_q.filter(Customer.upload_id == uid)
    all_zips = zip_q.group_by(Customer.zip).all()
    available_zips = sorted([z for z, _ in all_zips if z])
    selected = zip_code or (available_zips[0] if available_zips else None)

    ref = db.query(ZipIntelligence).filter(ZipIntelligence.zip == selected).first() if selected else None
    rows = _customer_query(db, upload_id, zip_code=selected).limit(ZIP_CUSTOMER_PREVIEW_LIMIT).all() if selected else []

    expected_revenue = sum(i.expected_revenue or 0 for _, i in rows)
    priorities = [_index_level(i.campaign_priority) for _, i in rows]
    priority = "High" if priorities.count("High") > len(priorities) / 2 else "Medium" if priorities.count("Medium") > 0 else "Low"

    prizm_dist = Counter(i.prizm_proxy_segment or "Unknown" for _, i in rows)
    ceragem_dist = Counter(i.ceragem_segment or "Unknown" for _, i in rows)
    pp_dist = Counter(_index_level(i.purchase_power_index) for _, i in rows)
    pain_dist = Counter(_index_level(i.pain_index) for _, i in rows)
    lifestyle_dist = Counter(_index_level(i.lifestyle_index) for _, i in rows)

    return {
        "selected_zip": selected,
        "available_zips": available_zips[:100],
        "summary": {
            "zip": selected,
            "city": (ref.city if ref and ref.city else None) or (rows[0][0].city if rows else "—"),
            "state": (ref.state if ref and ref.state else None) or (rows[0][0].state if rows else "—"),
            "median_income": ref.median_income if ref else None,
            "target_customers": len(rows),
            "expected_revenue": round(expected_revenue, 2),
            "campaign_priority": priority,
        },
        "income_intelligence": {
            "median_income": ref.median_income if ref else None,
            "top_50_income_zip": ref.top50_rank if ref else False,
            "population": ref.population if ref else None,
            "county": ref.county if ref else None,
            "reference_source": "zip_intelligence",
        },
        "sellable_products": _zip_sellable_products(db, uid, selected),
        "customer_intelligence": {
            "prizm_distribution": dict(prizm_dist),
            "ceragem_distribution": dict(ceragem_dist),
            "pain_index": dict(pain_dist),
            "lifestyle": dict(lifestyle_dist),
            "purchase_power": dict(pp_dist),
        },
        "campaign_opportunity": [
            {"type": "Premium Opportunity", "score": pp_dist.get("High", 0), "label": "High purchase power households"},
            {"type": "Wellness Opportunity", "score": ceragem_dist.get("High + Wellness", 0) + ceragem_dist.get("Mid-High + Wellness", 0), "label": "Wellness-oriented segments"},
            {"type": "Pain Opportunity", "score": pain_dist.get("High", 0), "label": "High pain index customers"},
            {"type": "Consultation Opportunity", "score": len(rows), "label": "Total targetable customers"},
        ],
        "customers": [
            {
                "id": str(c.customer_id),
                "email": c.email,
                "prizm_proxy_segment": i.prizm_proxy_segment,
                "ceragem_segment": i.ceragem_segment,
                "purchase_power": _index_level(i.purchase_power_index),
                "recommended_product": i.recommended_product,
                "campaign_priority": _index_level(i.campaign_priority),
                "expected_revenue": round(i.expected_revenue or 0, 2),
            }
            for c, i in rows
        ],
    }


def get_zip_dashboard(db: Session, upload_id: str | None = None, zip_code: str | None = None) -> dict:
    scope = f"{DASHBOARD_BUILD_VERSION}:{upload_id or 'all'}:{zip_code or 'all'}"
    return cached_dashboard("zip", scope, lambda: _get_zip_dashboard(db, upload_id, zip_code))


def _get_zip_dashboard(db: Session, upload_id: str | None = None, zip_code: str | None = None) -> dict:
    uid = _parse_upload_id(upload_id)
    if uid and has_upload_rollup(db, uid):
        return _zip_dashboard_from_rollup(db, uid, zip_code)
    if uid is None and has_any_rollup(db):
        return _zip_dashboard_from_rollup(db, None, zip_code)
    return _zip_dashboard_sql(db, upload_id, zip_code)


def _product_kpis_sql(db: Session, upload_id: str | None, product: str) -> dict:
    uid = _parse_upload_id(upload_id)
    q = (
        db.query(
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_conversion),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(CustomerIntelligence.recommended_product == product)
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    count, orders, revenue = q.one()
    customers = int(count or 0)
    total_orders = float(orders or 0)
    total_revenue = float(revenue or 0)
    return {
        "expected_customers": customers,
        "expected_orders": round(total_orders, 2),
        "expected_revenue": round(total_revenue, 2),
        "average_conversion": round(total_orders / customers, 4) if customers else 0,
    }


def _product_best_states_sql(db: Session, upload_id: str | None, product: str, limit: int = 10) -> list[dict]:
    uid = _parse_upload_id(upload_id)
    q = (
        db.query(
            Customer.state,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(CustomerIntelligence.recommended_product == product)
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    rows = (
        q.group_by(Customer.state)
        .order_by(func.sum(CustomerIntelligence.expected_revenue).desc())
        .limit(limit)
        .all()
    )
    return [
        {"state": st or "Unknown", "revenue": round(float(revenue or 0), 2), "count": int(count or 0)}
        for st, count, revenue in rows
    ]


def _product_best_zips_sql(db: Session, upload_id: str | None, product: str, limit: int = 12) -> list[dict]:
    uid = _parse_upload_id(upload_id)
    q = (
        db.query(
            Customer.zip,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(CustomerIntelligence.recommended_product == product)
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    rows = (
        q.group_by(Customer.zip)
        .order_by(func.sum(CustomerIntelligence.expected_revenue).desc())
        .limit(limit)
        .all()
    )
    return [
        {"zip": zp or "Unknown", "revenue": round(float(revenue or 0), 2), "count": int(count or 0)}
        for zp, count, revenue in rows
    ]


def _product_segment_matrix_sql(db: Session, upload_id: str | None, product: str) -> list[dict]:
    uid = _parse_upload_id(upload_id)
    q = (
        db.query(
            CustomerIntelligence.ceragem_segment,
            CustomerIntelligence.prizm_proxy_segment,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_revenue),
            func.max(CustomerIntelligence.campaign_priority),
        )
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(CustomerIntelligence.recommended_product == product)
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    rows = q.group_by(CustomerIntelligence.ceragem_segment, CustomerIntelligence.prizm_proxy_segment).all()
    out = []
    for cs, ps, count, revenue, max_priority in rows:
        out.append({
            "ceragem_segment": cs or "Unknown",
            "prizm_segment": ps or "Unknown",
            "target_customers": int(count or 0),
            "expected_revenue": round(float(revenue or 0), 2),
            "campaign_priority": _index_level(float(max_priority) if max_priority is not None else None),
        })
    return out


def _product_dashboard_from_rollup(db: Session, upload_id: uuid.UUID | None, product: str) -> dict:
    selected = product
    if upload_id:
        q = (
            db.query(
                func.sum(UploadRollup.customer_count),
                func.sum(UploadRollup.expected_orders),
                func.sum(UploadRollup.expected_revenue),
            )
            .filter(UploadRollup.upload_id == upload_id, UploadRollup.dimension == "product", UploadRollup.key == selected)
        )
        count, orders, revenue = q.one()
        kpis = {
            "expected_customers": int(count or 0),
            "expected_orders": round(float(orders or 0), 2),
            "expected_revenue": round(float(revenue or 0), 2),
            "average_conversion": round(float(orders or 0) / int(count or 1), 4) if count else 0,
        }
        state_rows = (
            db.query(
                UploadRollup.scope,
                func.sum(UploadRollup.customer_count),
                func.sum(UploadRollup.expected_revenue),
            )
            .filter(UploadRollup.upload_id == upload_id, UploadRollup.dimension == "product", UploadRollup.key == selected)
            .group_by(UploadRollup.scope)
            .order_by(func.sum(UploadRollup.expected_revenue).desc())
            .limit(10)
            .all()
        )
        best_states = [
            {"state": scope, "revenue": round(float(rev or 0), 2), "count": int(cnt or 0)}
            for scope, cnt, rev in state_rows
        ]
    else:
        q = (
            db.query(
                func.sum(UploadRollup.customer_count),
                func.sum(UploadRollup.expected_orders),
                func.sum(UploadRollup.expected_revenue),
            )
            .filter(UploadRollup.dimension == "product", UploadRollup.key == selected)
        )
        count, orders, revenue = q.one()
        kpis = {
            "expected_customers": int(count or 0),
            "expected_orders": round(float(orders or 0), 2),
            "expected_revenue": round(float(revenue or 0), 2),
            "average_conversion": round(float(orders or 0) / int(count or 1), 4) if count else 0,
        }
        state_rows = (
            db.query(
                UploadRollup.scope,
                func.sum(UploadRollup.customer_count),
                func.sum(UploadRollup.expected_revenue),
            )
            .filter(UploadRollup.dimension == "product", UploadRollup.key == selected)
            .group_by(UploadRollup.scope)
            .order_by(func.sum(UploadRollup.expected_revenue).desc())
            .limit(10)
            .all()
        )
        best_states = [
            {"state": scope, "revenue": round(float(rev or 0), 2), "count": int(cnt or 0)}
            for scope, cnt, rev in state_rows
        ]

    upload_key = str(upload_id) if upload_id else None
    campaign_perf = []
    for cp in db.query(CampaignProduct).filter(CampaignProduct.product == selected).all():
        camp = db.query(Campaign).filter(Campaign.campaign_id == cp.campaign_id).first()
        campaign_perf.append({
            "campaign_id": cp.campaign_id,
            "campaign": camp.campaign_name if camp else cp.campaign_id,
            "revenue": round(cp.revenue or 0, 2),
            "conversion": cp.conversion,
            "roi": round((cp.revenue or 0) / max(cp.click, 1) / 100, 4) if cp.click else None,
            "ctr": cp.click_rate,
            "status": camp.status if camp else "completed",
        })

    return {
        "selected_product": selected,
        "products": PRODUCTS,
        "kpis": {
            **kpis,
            "campaign_count": len(campaign_perf),
        },
        "best_states": best_states,
        "best_zips": _product_best_zips_sql(db, upload_key, selected),
        "segment_matrix": _product_segment_matrix_sql(db, upload_key, selected),
        "campaign_performance": campaign_perf,
        "rollup_source": True,
    }


def get_product_dashboard(db: Session, upload_id: str | None = None, product: str | None = None) -> dict:
    selected = product or "Master V9"
    scope = f"{DASHBOARD_BUILD_VERSION}:{upload_id or 'all'}:{selected}"
    return cached_dashboard("product", scope, lambda: _get_product_dashboard(db, upload_id, selected))


def _get_product_dashboard(db: Session, upload_id: str | None = None, product: str | None = None) -> dict:
    selected = product or "Master V9"
    uid = _parse_upload_id(upload_id)
    if uid and has_upload_rollup(db, uid):
        return _product_dashboard_from_rollup(db, uid, selected)
    if uid is None and has_any_rollup(db):
        return _product_dashboard_from_rollup(db, None, selected)
    return _product_dashboard_sql(db, upload_id, selected)


def _product_dashboard_sql(db: Session, upload_id: str | None = None, product: str | None = None) -> dict:
    selected = product or "Master V9"
    kpis = _product_kpis_sql(db, upload_id, selected)
    campaign_perf = []
    for cp in db.query(CampaignProduct).filter(CampaignProduct.product == selected).all():
        camp = db.query(Campaign).filter(Campaign.campaign_id == cp.campaign_id).first()
        campaign_perf.append({
            "campaign_id": cp.campaign_id,
            "campaign": camp.campaign_name if camp else cp.campaign_id,
            "revenue": round(cp.revenue or 0, 2),
            "conversion": cp.conversion,
            "roi": round((cp.revenue or 0) / max(cp.click, 1) / 100, 4) if cp.click else None,
            "ctr": cp.click_rate,
            "status": camp.status if camp else "completed",
        })

    return {
        "selected_product": selected,
        "products": PRODUCTS,
        "kpis": {
            **kpis,
            "campaign_count": len(campaign_perf),
        },
        "best_states": _product_best_states_sql(db, upload_id, selected),
        "best_zips": _product_best_zips_sql(db, upload_id, selected),
        "segment_matrix": _product_segment_matrix_sql(db, upload_id, selected),
        "campaign_performance": campaign_perf,
    }


def get_roi_dashboard(db: Session) -> dict:
    return cached_dashboard("roi", f"{DASHBOARD_BUILD_VERSION}:all", lambda: _get_roi_dashboard(db))


def _get_roi_dashboard(db: Session) -> dict:
    totals = db.query(
        func.sum(CampaignState.revenue),
        func.sum(CampaignState.cost),
        func.sum(CampaignState.click),
    ).one()
    total_revenue = float(totals[0] or 0)
    total_cost = float(totals[1] or 0)
    gross_margin = total_revenue - total_cost
    roi = round(gross_margin / total_cost, 4) if total_cost else None
    total_clicks = int(totals[2] or 0)
    cpa = round(total_cost / max(total_clicks * 0.02, 1), 2) if total_cost else None
    cpc = round(total_cost / max(total_clicks, 1), 2) if total_cost else None
    le_frame = round(le_frame_incentive(total_revenue), 2)
    expected_revenue = float(
        db.query(func.sum(UploadRollup.expected_revenue))
        .filter(UploadRollup.dimension == "state", UploadRollup.scope == "*")
        .scalar()
        or 0
    )
    if expected_revenue == 0:
        expected_revenue = float(
            db.query(func.sum(CustomerIntelligence.expected_revenue)).scalar() or 0
        )

    campaign_rows = (
        db.query(
            CampaignState.campaign_id,
            func.sum(CampaignState.revenue),
            func.sum(CampaignState.cost),
            func.sum(CampaignState.conversion),
            func.sum(CampaignState.click),
        )
        .group_by(CampaignState.campaign_id)
        .all()
    )
    campaigns = {c.campaign_id: c for c in db.query(Campaign).all()}

    roi_chart = []
    ranking = []
    for cid, revenue, cost, conversion, clicks in campaign_rows:
        camp = campaigns.get(cid)
        rev = float(revenue or 0)
        cst = float(cost or 0)
        camp_roi = round((rev - cst) / cst, 4) if cst else None
        roi_chart.append({
            "campaign": camp.campaign_name if camp else cid,
            "roi": camp_roi or 0,
            "revenue": round(rev, 2),
            "cost": round(cst, 2),
        })
        ranking.append({
            "campaign_id": cid,
            "campaign": camp.campaign_name if camp else cid,
            "revenue": round(rev, 2),
            "roi": camp_roi,
            "conversion": round(float(conversion or 0), 4),
            "expected_revenue": round(rev * 1.1, 2),
            "campaign_score": round((camp_roi or 0.5) * 100),
        })

    ranking.sort(key=lambda x: -(x["roi"] or 0))

    return {
        "kpis": {
            "revenue": round(total_revenue, 2),
            "gross_margin": round(gross_margin, 2),
            "roi": roi,
            "cpa": cpa,
            "cpc": cpc,
            "le_frame_incentive": le_frame,
            "campaign_cost": round(total_cost, 2),
            "expected_revenue": round(expected_revenue, 2),
        },
        "roi_chart": sorted(roi_chart, key=lambda x: x["campaign"]),
        "revenue_breakdown": [
            {"category": "Revenue", "value": round(total_revenue, 2)},
            {"category": "Cost", "value": round(total_cost, 2)},
            {"category": "Margin", "value": round(gross_margin, 2)},
            {"category": "Incentive", "value": le_frame},
        ],
        "campaign_ranking": ranking,
        "rollup_source": expected_revenue > 0 and has_any_rollup(db),
    }


def get_export_preview(
    db: Session,
    provider: str = "Generic CSV",
    upload_id: str | None = None,
    state_filter: str | None = None,
    zip_filter: str | None = None,
    segment_filter: str | None = None,
    product_filter: str | None = None,
) -> dict:
    q = _customer_query(db, upload_id, state=state_filter, zip_code=zip_filter, product=product_filter)
    if segment_filter:
        q = q.filter(CustomerIntelligence.prizm_proxy_segment == segment_filter)
    count = q.count()

    templates = (
        db.query(ExportTemplate)
        .filter(ExportTemplate.provider == provider)
        .order_by(ExportTemplate.order)
        .all()
    )
    if not templates:
        templates = (
            db.query(ExportTemplate)
            .filter(ExportTemplate.provider == "Generic CSV")
            .order_by(ExportTemplate.order)
            .all()
        )

    fields = [t.target_name for t in templates] + [
        "PRIZM Proxy Segment", "Ceragem Segment", "Message Direction", "Recommended Product",
        "Promo Code", "Recommended Promotion", "Price Resistance Score", "Commercial Version",
        "Campaign ID", "Campaign Name",
    ]
    est_bytes = count * len(fields) * 24

    return {
        "target_customers": count,
        "provider": provider,
        "export_fields": fields,
        "field_count": len(fields),
        "estimated_file_size_kb": round(est_bytes / 1024, 1),
        "estimated_download_seconds": max(1, round(est_bytes / (500 * 1024))),
    }


def get_settings_info(db: Session) -> dict:
    uploads = db.query(RawUpload).order_by(RawUpload.uploaded_date.desc()).limit(10).all()
    exports = db.query(ExportJob).order_by(ExportJob.created_at.desc()).limit(10).all()
    campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).limit(10).all()

    return {
        "general": {
            "company": "Ceragem USA",
            "timezone": "America/New_York",
            "currency": "USD",
            "language": "English (US)",
        },
        "intelligence": {
            "rule_version": "Volume 04 — Rules 001–070",
            "mapping_version": "Chapter 6 — DB-driven field mapping",
            "reference_data_version": get_reference_version(db)["libraryVersion"],
            "campaign_default": "Email — Wellness Priority",
        },
        "roles": ["Administrator", "Marketing", "Analyst", "Read Only"],
        "audit": {
            "upload_history": [
                {"file_name": u.filename, "status": u.status, "date": u.uploaded_date.isoformat() if u.uploaded_date else None}
                for u in uploads
            ],
            "export_history": [
                {"provider": e.provider, "campaign": e.campaign, "date": e.created_at.isoformat()}
                for e in exports
            ],
            "campaign_history": [
                {"campaign": c.campaign_name, "status": c.status, "date": c.created_at.isoformat()}
                for c in campaigns
            ],
            "rule_version_history": [
                {"version": "Volume 04 v1.0", "date": "2026-01-01"},
                {"version": "Chapter 6 Schema", "date": "2026-02-01"},
            ],
        },
    }
