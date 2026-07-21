"""Enrich state/metro dashboards with demographics, geo intelligence, TAM/TOM."""

from __future__ import annotations

import json
import uuid
from collections import Counter, defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.campaign.executive_dashboard import _state_geo_bundle_by_state
from app.campaign.opportunity_score import compute_state_opportunity_score
from app.market.cbsa_reference import (
    TOP_30_CBSAS,
    asian_relative_index,
    cbsa_meta,
    resolve_cbsa,
    state_asian_pct_estimate,
)
from app.market.tam_tom import compute_market_sizing
from app.models.customer import Customer, CustomerIntelligence
from app.models.scale import UploadRollup
from app.models.zip import ZipIntelligence


def _parse_upload_id(upload_id: str | uuid.UUID | None) -> uuid.UUID | None:
    if upload_id is None:
        return None
    if isinstance(upload_id, uuid.UUID):
        return upload_id
    return uuid.UUID(str(upload_id))


def _state_population_from_zips(db: Session, state: str | None) -> int | None:
    if not state:
        return None
    total = (
        db.query(func.sum(ZipIntelligence.population))
        .filter(ZipIntelligence.state == state, ZipIntelligence.population.isnot(None))
        .scalar()
    )
    return int(total) if total else None


def _state_median_income(db: Session, state: str | None) -> float | None:
    if not state:
        return None
    avg = (
        db.query(func.avg(ZipIntelligence.median_income))
        .filter(ZipIntelligence.state == state, ZipIntelligence.median_income.isnot(None))
        .scalar()
    )
    return round(float(avg), 2) if avg is not None else None


def _segment_revenue_from_rollups(db: Session, upload_id: uuid.UUID | None, state: str | None) -> dict:
    q = db.query(UploadRollup).filter(UploadRollup.dimension.in_(("ceragem_prod", "pp_band_prod", "product")))
    if upload_id:
        q = q.filter(UploadRollup.upload_id == upload_id)
    ceragem: dict[str, dict] = defaultdict(lambda: {"customers": 0, "revenue": 0.0})
    pp_band: dict[str, dict] = defaultdict(lambda: {"customers": 0, "revenue": 0.0})
    products: dict[str, dict] = defaultdict(lambda: {"customers": 0, "revenue": 0.0, "orders": 0.0})

    for row in q.all():
        if state and row.scope not in ("*", state):
            continue
        if row.dimension == "ceragem_prod" and row.key:
            segment = row.key.split("\x1f")[0]
            ceragem[segment]["customers"] += row.customer_count or 0
            ceragem[segment]["revenue"] += row.expected_revenue or 0
        elif row.dimension == "pp_band_prod" and row.key:
            band = row.key.split("\x1f")[0]
            pp_band[band]["customers"] += row.customer_count or 0
            pp_band[band]["revenue"] += row.expected_revenue or 0
        elif row.dimension == "product" and (not state or row.scope == state):
            products[row.key]["customers"] += row.customer_count or 0
            products[row.key]["revenue"] += row.expected_revenue or 0
            products[row.key]["orders"] += row.expected_orders or 0

    return {
        "ceragem": {k: dict(v) for k, v in ceragem.items()},
        "pp_band": {k: dict(v) for k, v in pp_band.items()},
        "products": {k: dict(v) for k, v in products.items()},
    }


def enrich_state_dashboard(
    db: Session,
    payload: dict,
    upload_id: str | uuid.UUID | None,
) -> dict:
    uid = _parse_upload_id(upload_id)
    selected = payload.get("selected_state")
    if not selected:
        return payload

    kpis = payload.get("kpis") or {}
    segments = payload.get("segment_distribution") or {}

    geo_bundle = _state_geo_bundle_by_state(db, uid)
    geo = geo_bundle.get(selected, {})

    pop = _state_population_from_zips(db, selected)
    median_income = _state_median_income(db, selected)
    asian_pct = state_asian_pct_estimate(selected)

    ceragem_counts = segments.get("ceragem") or {}
    pp_counts = segments.get("purchase_power") or {}
    segment_revenue = _segment_revenue_from_rollups(db, uid, selected)

    market_sizing = compute_market_sizing(
        population=pop,
        target_customers=int(kpis.get("target_customers") or 0),
        expected_revenue=float(kpis.get("expected_revenue") or 0),
        expected_orders=float(kpis.get("expected_orders") or 0),
        ceragem_segments=ceragem_counts,
        purchase_power_bands=pp_counts,
    )

    zip_rows = payload.get("zip_opportunity") or []
    if selected and zip_rows:
        zips = [z["zip"] for z in zip_rows if z.get("zip")]
        refs = db.query(ZipIntelligence).filter(ZipIntelligence.zip.in_(zips)).all() if zips else []
        ref_by_zip = {r.zip: r for r in refs}
        enriched_zips = []
        for row in zip_rows:
            ref = ref_by_zip.get(row["zip"])
            enriched = dict(row)
            if ref:
                enriched["median_income"] = ref.median_income
                enriched["population"] = ref.population
                enriched["asian_relative_index"] = asian_relative_index(ref.state, ref.city)
            enriched_zips.append(enriched)
        payload = {**payload, "zip_opportunity": enriched_zips}

    payload["demographics"] = {
        "median_household_income": median_income,
        "population": pop,
        "asian_population_pct": asian_pct,
        "asian_relative_index": round(asian_pct / 5.9, 2) if asian_pct else None,
        "income_bands": segments.get("purchase_power") or {},
    }
    payload["geo_intelligence"] = {
        "lifestyle_score": geo.get("lifestyle_score"),
        "lifestyle_tier": geo.get("lifestyle_tier"),
        "purchase_power_score": geo.get("purchase_power_score"),
        "purchase_power_tier": geo.get("purchase_power_tier"),
        "pain_index_score": geo.get("pain_index_score"),
        "pain_index_tier": geo.get("pain_index_tier"),
        "brand_score": geo.get("brand_score"),
        "brand_familiarity_tier": geo.get("brand_familiarity_tier"),
        "brand_enclave_pct": geo.get("brand_enclave_pct"),
        "digital_score": geo.get("digital_score"),
        "digital_engagement_tier": geo.get("digital_engagement_tier"),
        "opportunity_score": geo.get("opportunity_score"),
    }
    payload["market_sizing"] = market_sizing
    payload["segment_revenue"] = segment_revenue
    payload["sellable_products"] = [
        {
            "product": product,
            "expected_customers": stats["customers"],
            "expected_revenue": round(stats["revenue"], 2),
            "expected_orders": round(stats.get("orders", 0), 2),
        }
        for product, stats in sorted(segment_revenue.get("products", {}).items(), key=lambda x: -x[1]["revenue"])
        if stats["customers"] > 0
    ]
    return payload


def _metro_stats_from_rollups(db: Session, upload_id: uuid.UUID | None) -> dict[str, dict]:
    q = db.query(UploadRollup).filter(UploadRollup.dimension == "metro")
    if upload_id:
        q = q.filter(UploadRollup.upload_id == upload_id)

    # A CBSA can appear once per upload. For the "all" scope (upload_id is None) we sum every
    # upload's rows per CBSA so the rollup path matches the live aggregation (which scans all
    # customers), instead of the last row silently overwriting the others.
    _dist_dims = ("ceragem", "purchase_power", "lifestyle", "prizm", "pain_index", "brand_familiarity")
    agg: dict[str, dict] = {}
    for row in q.all():
        payload = {}
        if row.payload_json:
            try:
                payload = json.loads(row.payload_json)
            except json.JSONDecodeError:
                payload = {}
        bucket = agg.get(row.key)
        if bucket is None:
            bucket = {
                "customers": 0,
                "orders": 0.0,
                "revenue": 0.0,
                "states": set(),
                "products": defaultdict(lambda: {"customers": 0, "revenue": 0.0, "orders": 0.0}),
                "zip_revenue": defaultdict(float),
                **{dim: Counter() for dim in _dist_dims},
            }
            agg[row.key] = bucket
        bucket["customers"] += int(row.customer_count or 0)
        bucket["orders"] += float(row.expected_orders or 0)
        bucket["revenue"] += float(row.expected_revenue or 0)
        for st in payload.get("states") or []:
            bucket["states"].add(st)
        for dim in _dist_dims:
            for k, v in (payload.get(dim) or {}).items():
                bucket[dim][k] += v
        for p in payload.get("products") or []:
            name = p.get("product")
            if not name:
                continue
            slot = bucket["products"][name]
            slot["customers"] += int(p.get("customers", 0) or 0)
            slot["revenue"] += float(p.get("revenue", 0) or 0)
            slot["orders"] += float(p.get("orders", 0) or 0)
        for z in payload.get("top_zips") or []:
            zc = z.get("zip")
            if zc:
                bucket["zip_revenue"][zc] += float(z.get("expected_revenue", 0) or 0)

    stats: dict[str, dict] = {}
    for code, bucket in agg.items():
        products = sorted(
            (
                {
                    "product": name,
                    "customers": d["customers"],
                    "revenue": round(d["revenue"], 2),
                    "orders": round(d["orders"], 2),
                }
                for name, d in bucket["products"].items()
            ),
            key=lambda x: -x["customers"],
        )[:8]
        top_zips = [
            {"zip": z, "expected_revenue": round(rev, 2)}
            for z, rev in sorted(bucket["zip_revenue"].items(), key=lambda x: -x[1])[:10]
        ]
        stats[code] = {
            "customers": bucket["customers"],
            "orders": bucket["orders"],
            "revenue": bucket["revenue"],
            "states": sorted(bucket["states"]),
            "top_product": products[0]["product"] if products else None,
            "ceragem": dict(bucket["ceragem"]),
            "purchase_power": dict(bucket["purchase_power"]),
            "lifestyle": dict(bucket["lifestyle"]),
            "prizm": dict(bucket["prizm"]),
            "pain_index": dict(bucket["pain_index"]),
            "brand_familiarity": dict(bucket["brand_familiarity"]),
            "top_zips": top_zips,
            "products": products,
        }
    return stats


def _pp_band(val: float | None) -> str:
    if val is None:
        return "Low"
    if val >= 0.75:
        return "High"
    if val >= 0.45:
        return "Medium"
    return "Low"


_BAND_SCORE_PTS = {"High": 75.0, "Medium": 55.0, "Low": 25.0}


def _bands_weighted_score(bands: dict | None) -> float:
    """Convert a High/Medium/Low band count distribution to a 0-100 axis score."""
    if not bands:
        return 45.0
    total = sum(bands.values())
    if total <= 0:
        return 45.0
    return sum(_BAND_SCORE_PTS.get(str(k), 45.0) * float(v) for k, v in bands.items()) / total


def _metro_sellable_products(
    products: list[dict], customers: int, revenue: float, orders: float
) -> list[dict]:
    """Metro product mix using actual per-product revenue/orders (like state/ZIP).

    Legacy rollups stored only per-product customer counts, so fall back to
    proportional allocation when revenue/orders are absent from the payload.
    """
    result = []
    for p in products:
        cust = p.get("customers", 0)
        rev = p.get("revenue")
        ords = p.get("orders")
        if rev is None:
            rev = revenue * (cust / customers) if customers else 0.0
        if ords is None:
            ords = orders * (cust / customers) if customers else 0.0
        result.append(
            {
                "product": p["product"],
                "expected_customers": cust,
                "expected_revenue": round(rev, 2),
                "expected_orders": round(ords, 2),
            }
        )
    return result


def _aggregate_metro_customer_stats(db: Session, upload_id: uuid.UUID | None) -> dict[str, dict]:
    """Live CBSA aggregation from customers (fallback when metro rollups are missing)."""
    agg: dict[str, dict] = defaultdict(
        lambda: {
            "customers": 0,
            "orders": 0.0,
            "revenue": 0.0,
            "states": set(),
            "ceragem": Counter(),
            "purchase_power": Counter(),
            "lifestyle": Counter(),
            "prizm": Counter(),
            "pain_index": Counter(),
            "brand_familiarity": Counter(),
            "products": Counter(),
            "product_revenue": defaultdict(float),
            "product_orders": defaultdict(float),
            "zip_revenue": defaultdict(float),
        }
    )

    q = (
        db.query(
            Customer.state,
            Customer.city,
            Customer.zip,
            CustomerIntelligence.expected_conversion,
            CustomerIntelligence.expected_revenue,
            CustomerIntelligence.ceragem_segment,
            CustomerIntelligence.purchase_power_index,
            CustomerIntelligence.lifestyle_index,
            CustomerIntelligence.recommended_product,
            CustomerIntelligence.prizm_proxy_segment,
            CustomerIntelligence.pain_index,
            CustomerIntelligence.brand_familiarity_index,
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)

    for (
        state,
        city,
        zip_code,
        orders,
        revenue,
        ceragem,
        pp,
        lifestyle,
        product,
        prizm,
        pain,
        brand,
    ) in q.all():
        code = resolve_cbsa(state, city, zip_code)
        if not code or not cbsa_meta(code):
            continue
        bucket = agg[code]
        bucket["customers"] += 1
        bucket["orders"] += float(orders or 0)
        bucket["revenue"] += float(revenue or 0)
        if state:
            bucket["states"].add(state)
        if ceragem:
            bucket["ceragem"][ceragem] += 1
        bucket["purchase_power"][_pp_band(pp)] += 1
        bucket["lifestyle"][_pp_band(lifestyle)] += 1
        if prizm:
            bucket["prizm"][prizm] += 1
        if pain is not None:
            bucket["pain_index"][_pp_band(pain)] += 1
        if brand is not None:
            bucket["brand_familiarity"][_pp_band(brand)] += 1
        if product:
            bucket["products"][product] += 1
            bucket["product_revenue"][product] += float(revenue or 0)
            bucket["product_orders"][product] += float(orders or 0)
        if zip_code:
            bucket["zip_revenue"][zip_code] += float(revenue or 0)

    stats: dict[str, dict] = {}
    for code, bucket in agg.items():
        top_product = bucket["products"].most_common(1)[0][0] if bucket["products"] else None
        top_zips = [
            {"zip": z, "expected_revenue": round(rev, 2)}
            for z, rev in sorted(bucket["zip_revenue"].items(), key=lambda x: -x[1])[:10]
        ]
        stats[code] = {
            "customers": bucket["customers"],
            "orders": bucket["orders"],
            "revenue": bucket["revenue"],
            "states": sorted(bucket["states"]),
            "top_product": top_product,
            "ceragem": dict(bucket["ceragem"]),
            "purchase_power": dict(bucket["purchase_power"]),
            "lifestyle": dict(bucket["lifestyle"]),
            "prizm": dict(bucket["prizm"]),
            "pain_index": dict(bucket["pain_index"]),
            "brand_familiarity": dict(bucket["brand_familiarity"]),
            "top_zips": top_zips,
            "products": [
                {
                    "product": name,
                    "customers": count,
                    "revenue": round(bucket["product_revenue"].get(name, 0.0), 2),
                    "orders": round(bucket["product_orders"].get(name, 0.0), 2),
                }
                for name, count in bucket["products"].most_common(8)
            ],
        }
    return stats


def get_metro_dashboard(db: Session, upload_id: str | uuid.UUID | None = None, cbsa: str | None = None) -> dict:
    uid = _parse_upload_id(upload_id)
    metro_stats = _metro_stats_from_rollups(db, uid)
    live_source = False
    if not metro_stats:
        metro_stats = _aggregate_metro_customer_stats(db, uid)
        live_source = bool(metro_stats)

    metros = []
    for rank, ref in enumerate(TOP_30_CBSAS, start=1):
        code = ref["code"]
        stats = metro_stats.get(code, {"customers": 0, "orders": 0.0, "revenue": 0.0})
        customers = stats["customers"]
        orders = stats["orders"]
        revenue = stats["revenue"]
        conversion = orders / customers if customers else 0.0
        ceragem = stats.get("ceragem") or {}
        pp = stats.get("purchase_power") or {}

        market_sizing = compute_market_sizing(
            population=ref["population"],
            target_customers=customers,
            expected_revenue=revenue,
            expected_orders=orders,
            ceragem_segments=ceragem,
            purchase_power_bands=pp,
        )

        metros.append(
            {
                "rank": rank,
                "cbsa_code": code,
                "cbsa_name": ref["name"],
                "states": list(ref["states"]),
                "target_customers": customers,
                "expected_revenue": round(revenue, 2),
                "expected_orders": round(orders, 2),
                "conversion": round(conversion, 6),
                "demographics": {
                    "population": ref["population"],
                    "median_household_income": ref["median_income"],
                    "asian_population_pct": ref["asian_pct"],
                    "asian_relative_index": round(ref["asian_pct"] / 5.9, 2),
                },
                "segment_distribution": {
                    "ceragem": ceragem,
                    "purchase_power": pp,
                    "lifestyle": stats.get("lifestyle") or {},
                    "prizm": stats.get("prizm") or {},
                    "pain_index": stats.get("pain_index") or {},
                    "brand_familiarity": stats.get("brand_familiarity") or {},
                },
                "market_sizing": market_sizing,
                "top_product": stats.get("top_product"),
                "top_zips": stats.get("top_zips") or [],
                "sellable_products": _metro_sellable_products(
                    stats.get("products") or [], customers, revenue, orders
                ),
                "opportunity_score": 0.0,
            }
        )

    # Opportunity Score uses the shared state-level blend (intelligence axes + revenue share +
    # conversion + product fit), so metros always surface a comparable 8-99 value.
    max_rev = max((m["expected_revenue"] for m in metros), default=0.0)
    for m in metros:
        if not m["target_customers"]:
            m["opportunity_score"] = 0.0
            continue
        sd = m["segment_distribution"]
        m["opportunity_score"] = compute_state_opportunity_score(
            {
                "conversion": m["conversion"],
                "revenue": m["expected_revenue"],
                "pain_index_score": _bands_weighted_score(sd.get("pain_index")),
                "purchase_power_score": _bands_weighted_score(sd.get("purchase_power")),
                "lifestyle_score": _bands_weighted_score(sd.get("lifestyle")),
                "brand_score": _bands_weighted_score(sd.get("brand_familiarity")),
                "digital_score": 45.0,
                "top_product": m.get("top_product"),
            },
            max_revenue=max_rev,
        )

    metros.sort(key=lambda m: (-m["expected_revenue"], -m["target_customers"], m["rank"]))

    selected = None
    if cbsa:
        selected = next((m for m in metros if m["cbsa_code"] == cbsa), None)

    return {
        "selected_metro": selected,
        "metros": metros,
        "available_metros": [{"cbsa_code": m["cbsa_code"], "cbsa_name": m["cbsa_name"]} for m in metros],
        "data_vintage": "2022-acs",
        "rollup_source": bool(metro_stats) and not live_source,
        "live_source": live_source,
    }


def build_metro_rollups_for_upload(db: Session, upload_id: uuid.UUID | str) -> int:
    """Aggregate customer metrics by CBSA for an upload (called from rollup build)."""
    uid = _parse_upload_id(upload_id)
    if not uid:
        return 0

    db.query(UploadRollup).filter(UploadRollup.upload_id == uid, UploadRollup.dimension == "metro").delete()
    metro_stats = _aggregate_metro_customer_stats(db, uid)

    added = 0
    for code, stats in metro_stats.items():
        meta = cbsa_meta(code)
        payload = {
            "states": stats.get("states", []),
            "top_product": stats.get("top_product"),
            "ceragem": stats.get("ceragem", {}),
            "purchase_power": stats.get("purchase_power", {}),
            "lifestyle": stats.get("lifestyle", {}),
            "prizm": stats.get("prizm", {}),
            "pain_index": stats.get("pain_index", {}),
            "brand_familiarity": stats.get("brand_familiarity", {}),
            "top_zips": stats.get("top_zips", []),
            "products": stats.get("products", []),
            "cbsa_name": meta["name"] if meta else code,
        }
        db.add(
            UploadRollup(
                upload_id=uid,
                dimension="metro",
                scope="*",
                key=code,
                customer_count=stats["customers"],
                expected_orders=stats["orders"],
                expected_revenue=stats["revenue"],
                payload_json=json.dumps(payload),
            )
        )
        added += 1
    return added
