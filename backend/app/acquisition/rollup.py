"""Phase 1 — Pre-aggregate upload metrics for dashboard performance."""

from __future__ import annotations

import json
import uuid
from collections import defaultdict

from sqlalchemy import case, func, literal
from sqlalchemy.orm import Session

from app.models.customer import Customer, CustomerIntelligence
from app.models.scale import UploadRollup

DISTRIBUTION_ROLLUP_DIMENSIONS = ("ceragem_prod", "pp_band", "pp_band_prod")
ROLLUP_KEY_SEP = "\x1f"


def _index_level(value: float | None) -> str:
    if value is None:
        return "Low"
    if value >= 0.75:
        return "High"
    if value >= 0.45:
        return "Medium"
    return "Low"


def _income_band_case():
    pp = CustomerIntelligence.purchase_power_index
    return case(
        (pp >= 0.75, "$150K+"),
        (pp >= 0.60, "$100K–$150K"),
        (pp >= 0.45, "$75K–$100K"),
        (pp >= 0.30, "$50K–$75K"),
        else_="<$50K",
    )


def _as_upload_uuid(upload_id: uuid.UUID | str) -> uuid.UUID:
    if isinstance(upload_id, uuid.UUID):
        return upload_id
    return uuid.UUID(str(upload_id))


def has_upload_rollup(db: Session, upload_id: uuid.UUID | str) -> bool:
    uid = _as_upload_uuid(upload_id)
    return (
        db.query(UploadRollup.id)
        .filter(UploadRollup.upload_id == uid)
        .limit(1)
        .first()
        is not None
    )


def clear_upload_rollup(db: Session, upload_id: uuid.UUID | str) -> None:
    uid = _as_upload_uuid(upload_id)
    db.query(UploadRollup).filter(UploadRollup.upload_id == uid).delete()


def build_upload_rollup(db: Session, upload_id: uuid.UUID | str) -> int:
    """Build rollup rows using SQL aggregates — never loads trace_json."""
    uid = _as_upload_uuid(upload_id)
    clear_upload_rollup(db, uid)
    rows_added = 0

    state_stats = (
        db.query(
            Customer.state,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_conversion),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(Customer.upload_id == uid)
        .group_by(Customer.state)
        .all()
    )
    for state, count, orders, revenue in state_stats:
        db.add(
            UploadRollup(
                upload_id=uid,
                dimension="state",
                scope="*",
                key=state or "Unknown",
                customer_count=int(count or 0),
                expected_orders=float(orders or 0),
                expected_revenue=float(revenue or 0),
            )
        )
        rows_added += 1

    segment_dims = (
        ("prizm", CustomerIntelligence.prizm_proxy_segment),
        ("ceragem", CustomerIntelligence.ceragem_segment),
        ("product", CustomerIntelligence.recommended_product),
    )
    for dimension, column in segment_dims:
        grouped = (
            db.query(
                Customer.state,
                column,
                func.count(Customer.customer_id),
                func.sum(CustomerIntelligence.expected_conversion),
                func.sum(CustomerIntelligence.expected_revenue),
            )
            .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
            .filter(Customer.upload_id == uid)
            .group_by(Customer.state, column)
            .all()
        )
        for state, key, count, orders, revenue in grouped:
            db.add(
                UploadRollup(
                    upload_id=uid,
                    dimension=dimension,
                    scope=state or "Unknown",
                    key=str(key or "Unknown"),
                    customer_count=int(count or 0),
                    expected_orders=float(orders or 0),
                    expected_revenue=float(revenue or 0),
                )
            )
            rows_added += 1

    band_case = _income_band_case()
    pp_band_stats = (
        db.query(
            band_case.label("band"),
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(Customer.upload_id == uid)
        .group_by(band_case)
        .all()
    )
    for band, count, revenue in pp_band_stats:
        db.add(
            UploadRollup(
                upload_id=uid,
                dimension="pp_band",
                scope="*",
                key=str(band or "<$50K"),
                customer_count=int(count or 0),
                expected_orders=0.0,
                expected_revenue=float(revenue or 0),
            )
        )
        rows_added += 1

    pp_product_stats = (
        db.query(
            band_case.label("band"),
            CustomerIntelligence.recommended_product,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(
            Customer.upload_id == uid,
            CustomerIntelligence.recommended_product.isnot(None),
        )
        .group_by(band_case, CustomerIntelligence.recommended_product)
        .all()
    )
    for band, product, count, revenue in pp_product_stats:
        band_key = str(band or "<$50K")
        product_key = str(product or "Unknown")
        db.add(
            UploadRollup(
                upload_id=uid,
                dimension="pp_band_prod",
                scope="*",
                key=f"{band_key}{ROLLUP_KEY_SEP}{product_key}",
                customer_count=int(count or 0),
                expected_orders=0.0,
                expected_revenue=float(revenue or 0),
            )
        )
        rows_added += 1

    ceragem_product_stats = (
        db.query(
            CustomerIntelligence.ceragem_segment,
            CustomerIntelligence.recommended_product,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(
            Customer.upload_id == uid,
            CustomerIntelligence.ceragem_segment.isnot(None),
            CustomerIntelligence.recommended_product.isnot(None),
        )
        .group_by(CustomerIntelligence.ceragem_segment, CustomerIntelligence.recommended_product)
        .all()
    )
    for segment, product, count, revenue in ceragem_product_stats:
        segment_key = str(segment or "Unknown")
        product_key = str(product or "Unknown")
        db.add(
            UploadRollup(
                upload_id=uid,
                dimension="ceragem_prod",
                scope="*",
                key=f"{segment_key}{ROLLUP_KEY_SEP}{product_key}",
                customer_count=int(count or 0),
                expected_orders=0.0,
                expected_revenue=float(revenue or 0),
            )
        )
        rows_added += 1

    zip_agg: dict[tuple[str, str], dict] = defaultdict(
        lambda: {
            "count": 0,
            "orders": 0.0,
            "revenue": 0.0,
            "city": None,
            "purchase_power": "Low",
            "campaign_priority": "Low",
            "recommended_product": None,
        }
    )
    index_agg: dict[tuple[str, str, str], dict] = defaultdict(lambda: {"count": 0, "orders": 0.0, "revenue": 0.0})

    lightweight = (
        db.query(
            Customer.state,
            Customer.zip,
            Customer.city,
            CustomerIntelligence.expected_conversion,
            CustomerIntelligence.expected_revenue,
            CustomerIntelligence.purchase_power_index,
            CustomerIntelligence.pain_index,
            CustomerIntelligence.lifestyle_index,
            CustomerIntelligence.campaign_priority,
            CustomerIntelligence.recommended_product,
            CustomerIntelligence.brand_familiarity_index,
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(Customer.upload_id == uid)
        .all()
    )

    for row in lightweight:
        state, zip_code, city, orders, revenue, pp, pain, lifestyle, priority, product, brand = row
        state_key = state or "Unknown"
        zip_key = zip_code or "Unknown"
        bucket = zip_agg[(state_key, zip_key)]
        bucket["count"] += 1
        bucket["orders"] += float(orders or 0)
        bucket["revenue"] += float(revenue or 0)
        bucket["city"] = city or bucket["city"]
        pp_level = _index_level(pp)
        cp_level = _index_level(priority)
        if pp_level == "High":
            bucket["purchase_power"] = "High"
        elif pp_level == "Medium" and bucket["purchase_power"] != "High":
            bucket["purchase_power"] = "Medium"
        if cp_level == "High":
            bucket["campaign_priority"] = "High"
        elif cp_level == "Medium" and bucket["campaign_priority"] != "High":
            bucket["campaign_priority"] = "Medium"
        bucket["recommended_product"] = product or bucket["recommended_product"]

        for dimension, value in (
            ("purchase_power", pp),
            ("pain", pain),
            ("lifestyle", lifestyle),
            ("brand", brand),
        ):
            idx_key = (state_key, dimension, _index_level(value))
            idx_bucket = index_agg[idx_key]
            idx_bucket["count"] += 1
            idx_bucket["orders"] += float(orders or 0)
            idx_bucket["revenue"] += float(revenue or 0)

    for (state, zip_code), metrics in zip_agg.items():
        db.add(
            UploadRollup(
                upload_id=uid,
                dimension="zip",
                scope=state,
                key=zip_code,
                customer_count=metrics["count"],
                expected_orders=metrics["orders"],
                expected_revenue=metrics["revenue"],
                payload_json=json.dumps(
                    {
                        "city": metrics["city"],
                        "purchase_power": metrics["purchase_power"],
                        "campaign_priority": metrics["campaign_priority"],
                        "recommended_product": metrics["recommended_product"],
                    }
                ),
            )
        )
        rows_added += 1

    for (state, dimension, key), metrics in index_agg.items():
        db.add(
            UploadRollup(
                upload_id=uid,
                dimension=dimension,
                scope=state,
                key=key,
                customer_count=metrics["count"],
                expected_orders=metrics["orders"],
                expected_revenue=metrics["revenue"],
            )
        )
        rows_added += 1

    rows_added += build_city_rollups_for_upload(db, uid)

    db.flush()
    from app.market.market_intelligence import build_metro_rollups_for_upload

    rows_added += build_metro_rollups_for_upload(db, uid)
    return rows_added


def build_city_rollups_for_upload(db: Session, upload_id: uuid.UUID | str) -> int:
    """Per (state, city, product) rollup for the Revenue-by-City chart.

    The national dashboard previously aggregated cities from a capped top-N ZIP pool (~60% of
    revenue). This dimension pre-aggregates every customer by city+product so the national and
    state readers reflect 100% of revenue without a full-table scan. Customer-weighted sums of
    the geo indices are stored in the payload so exact averages can be recovered on read.
    """
    uid = _as_upload_uuid(upload_id)
    db.query(UploadRollup).filter(
        UploadRollup.upload_id == uid, UploadRollup.dimension == "city_prod"
    ).delete()

    city_expr = func.coalesce(Customer.city, literal("Unknown"))
    rows = (
        db.query(
            Customer.state,
            city_expr,
            CustomerIntelligence.recommended_product,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_conversion),
            func.sum(CustomerIntelligence.expected_revenue),
            func.sum(CustomerIntelligence.pain_index),
            func.sum(CustomerIntelligence.lifestyle_index),
            func.sum(CustomerIntelligence.purchase_power_index),
            func.sum(CustomerIntelligence.campaign_priority),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(Customer.upload_id == uid, CustomerIntelligence.recommended_product.isnot(None))
        .group_by(Customer.state, city_expr, CustomerIntelligence.recommended_product)
        .all()
    )

    added = 0
    for state, city, product, count, orders, revenue, pain_sum, life_sum, pp_sum, cp_sum in rows:
        city_name = str(city or "Unknown")
        product_name = str(product or "Unknown")
        db.add(
            UploadRollup(
                upload_id=uid,
                dimension="city_prod",
                scope=(state or "Unknown")[:16],
                key=f"{city_name}{ROLLUP_KEY_SEP}{product_name}"[:128],
                customer_count=int(count or 0),
                expected_orders=float(orders or 0),
                expected_revenue=float(revenue or 0),
                payload_json=json.dumps(
                    {
                        "city": city_name,
                        "product": product_name,
                        "pain_sum": float(pain_sum or 0),
                        "lifestyle_sum": float(life_sum or 0),
                        "pp_sum": float(pp_sum or 0),
                        "cp_sum": float(cp_sum or 0),
                    }
                ),
            )
        )
        added += 1
    return added


def has_distribution_rollups(db: Session, upload_id: uuid.UUID | str | None = None) -> bool:
    q = db.query(UploadRollup.id).filter(UploadRollup.dimension == "ceragem_prod")
    if upload_id is not None:
        q = q.filter(UploadRollup.upload_id == _as_upload_uuid(upload_id))
    return q.limit(1).first() is not None
