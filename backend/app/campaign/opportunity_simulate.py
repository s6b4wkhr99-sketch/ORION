"""Email campaign opportunity simulator — multi-SKU, multi-state, multi-segment."""

from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid

from sqlalchemy import case, func, literal, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.intelligence.ceragem_rules import parse_ceragem_tier
from app.intelligence.prizm_rules import PRIZM_SEGMENTS as PRIZM_SEGMENT_CODES
from app.models.customer import Customer, CustomerIntelligence

_SIMULATE_CACHE: dict[str, tuple[float, dict]] = {}
_SIMULATE_CACHE_LOCK = threading.Lock()

CERAGEM_TIER_LABELS: dict[str, str] = {
    "High+": "High",
    "Mid-High+": "Mid-High",
    "Mid+": "Mid",
    "Mid-Low+": "Mid-Low",
    "Low+": "Low",
}

CERAGEM_TIER_CODES: dict[str, str] = {label: code for code, label in CERAGEM_TIER_LABELS.items()}

CERAGEM_TIER_ORDER: tuple[str, ...] = ("High", "Mid-High", "Mid", "Mid-Low", "Low", "Unclassified")

VALID_PRIZM_SEGMENTS: frozenset[str] = frozenset(
    segment for segment in PRIZM_SEGMENT_CODES if segment not in {"Unknown", "Unclassified"}
)
PRIZM_SEGMENT_ORDER: tuple[str, ...] = tuple(
    segment for segment in PRIZM_SEGMENT_CODES if segment in VALID_PRIZM_SEGMENTS
) + ("Unclassified",)


def _index_band(column):
    return case(
        (column >= 0.75, literal("High")),
        (column >= 0.45, literal("Medium")),
        else_=literal("Low"),
    )


def _parse_upload_id(upload_id: str | None) -> uuid.UUID | None:
    return uuid.UUID(upload_id) if upload_id else None


def _base_query(db: Session, upload_id: str | None):
    uid = _parse_upload_id(upload_id)
    q = db.query(Customer, CustomerIntelligence).join(
        CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    return q


def _apply_skus(q, skus: list[str]):
    if not skus:
        return q
    return q.filter(CustomerIntelligence.recommended_product.in_(skus))


def _apply_states(q, states: list[str] | None):
    if not states:
        return q
    return q.filter(Customer.state.in_(states))


def _ceragem_tier_label(segment: str | None) -> str:
    if not segment or not str(segment).strip():
        return "Unclassified"
    tier = parse_ceragem_tier(str(segment))
    label = CERAGEM_TIER_LABELS.get(tier)
    if label:
        return label
    if tier.endswith("+") and tier[:-1] in {"High", "Mid-High", "Mid", "Mid-Low", "Low"}:
        return tier[:-1]
    if tier in CERAGEM_TIER_ORDER:
        return tier
    return "Unclassified"


def _ceragem_tier_filter(selected_tiers: list[str]):
    known_tier_conditions = []
    for code in CERAGEM_TIER_LABELS:
        legacy = code.rstrip("+")
        known_tier_conditions.append(CustomerIntelligence.ceragem_segment.like(f"{code}%"))
        known_tier_conditions.append(CustomerIntelligence.ceragem_segment.like(f"{legacy} +%"))
        known_tier_conditions.append(CustomerIntelligence.ceragem_segment.like(f"{legacy}+%"))

    conditions = []
    for label in selected_tiers:
        if label == "Unclassified":
            conditions.append(
                or_(
                    CustomerIntelligence.ceragem_segment.is_(None),
                    CustomerIntelligence.ceragem_segment == "",
                    ~or_(*known_tier_conditions),
                )
            )
            continue
        code = CERAGEM_TIER_CODES.get(label, label)
        legacy = code.rstrip("+")
        conditions.append(CustomerIntelligence.ceragem_segment.like(f"{code}%"))
        conditions.append(CustomerIntelligence.ceragem_segment.like(f"{legacy} +%"))
        conditions.append(CustomerIntelligence.ceragem_segment.like(f"{legacy}+%"))
    return or_(*conditions)


def _prizm_segment_label(segment: str | None) -> str:
    text = (segment or "").strip()
    if text in VALID_PRIZM_SEGMENTS:
        return text
    return "Unclassified"


def _prizm_segment_filter(selected_segments: list[str]):
    conditions = []
    for label in selected_segments:
        if label == "Unclassified":
            conditions.append(
                or_(
                    CustomerIntelligence.prizm_proxy_segment.is_(None),
                    CustomerIntelligence.prizm_proxy_segment == "",
                    ~CustomerIntelligence.prizm_proxy_segment.in_(list(VALID_PRIZM_SEGMENTS)),
                )
            )
            continue
        conditions.append(CustomerIntelligence.prizm_proxy_segment == label)
    return or_(*conditions)


def _apply_segment_filters(q, filters: dict | None):
    if not filters:
        return q
    ceragem = filters.get("ceragem") or []
    prizm = filters.get("prizm") or []
    lifestyle = filters.get("lifestyle") or []
    pain_index = filters.get("pain_index") or []
    purchase_power = filters.get("purchase_power") or []
    brand_familiarity = filters.get("brand_familiarity") or []

    if ceragem:
        q = q.filter(_ceragem_tier_filter(ceragem))
    if prizm:
        q = q.filter(_prizm_segment_filter(prizm))
    if lifestyle:
        q = q.filter(_index_band(CustomerIntelligence.lifestyle_index).in_(lifestyle))
    if pain_index:
        q = q.filter(_index_band(CustomerIntelligence.pain_index).in_(pain_index))
    if purchase_power:
        q = q.filter(_index_band(CustomerIntelligence.purchase_power_index).in_(purchase_power))
    if brand_familiarity:
        q = q.filter(_index_band(CustomerIntelligence.brand_familiarity_index).in_(brand_familiarity))
    return q


def _aggregate_kpis(q) -> dict:
    customers, revenue, conversion_sum = (
        q.with_entities(
            func.count(Customer.customer_id),
            func.coalesce(func.sum(CustomerIntelligence.expected_revenue), 0.0),
            func.coalesce(func.sum(CustomerIntelligence.expected_conversion), 0.0),
        ).one()
    )
    customers = int(customers or 0)
    revenue = round(float(revenue or 0), 2)
    orders = round(float(conversion_sum or 0), 2)
    conversion = round(orders / customers, 6) if customers else 0.0
    return {
        "customers": customers,
        "revenue": revenue,
        "orders": orders,
        "conversion": conversion,
    }


def _by_state(q) -> list[dict]:
    rows = (
        q.with_entities(
            Customer.state,
            func.count(Customer.customer_id),
            func.coalesce(func.sum(CustomerIntelligence.expected_revenue), 0.0),
            func.coalesce(func.sum(CustomerIntelligence.expected_conversion), 0.0),
        )
        .group_by(Customer.state)
        .all()
    )
    out = []
    for state, customers, revenue, orders in rows:
        if not state:
            continue
        customers = int(customers or 0)
        revenue = round(float(revenue or 0), 2)
        orders = round(float(orders or 0), 2)
        out.append(
            {
                "state": state,
                "customers": customers,
                "revenue": revenue,
                "orders": orders,
                "conversion": round(orders / customers, 6) if customers else 0.0,
            }
        )
    out.sort(key=lambda row: row["revenue"], reverse=True)
    return out


def _segment_distributions(q) -> dict:
    rows = q.with_entities(
        CustomerIntelligence.ceragem_segment,
        CustomerIntelligence.prizm_proxy_segment,
        CustomerIntelligence.lifestyle_index,
        CustomerIntelligence.pain_index,
        CustomerIntelligence.purchase_power_index,
        CustomerIntelligence.brand_familiarity_index,
    ).all()

    ceragem: dict[str, int] = {}
    prizm: dict[str, int] = {}
    lifestyle: dict[str, int] = {}
    pain_index: dict[str, int] = {}
    purchase_power: dict[str, int] = {}
    brand_familiarity: dict[str, int] = {}

    def _band(value: float | None) -> str:
        if value is None:
            return "Low"
        if float(value) >= 0.75:
            return "High"
        if float(value) >= 0.45:
            return "Medium"
        return "Low"

    for cer, pri, life, pain, pp, brand in rows:
        cer_label = _ceragem_tier_label(cer)
        ceragem[cer_label] = ceragem.get(cer_label, 0) + 1
        pri_label = _prizm_segment_label(pri)
        prizm[pri_label] = prizm.get(pri_label, 0) + 1
        life_label = _band(life)
        lifestyle[life_label] = lifestyle.get(life_label, 0) + 1
        pain_label = _band(pain)
        pain_index[pain_label] = pain_index.get(pain_label, 0) + 1
        pp_label = _band(pp)
        purchase_power[pp_label] = purchase_power.get(pp_label, 0) + 1
        brand_label = _band(brand)
        brand_familiarity[brand_label] = brand_familiarity.get(brand_label, 0) + 1

    return {
        "ceragem": ceragem,
        "prizm": prizm,
        "lifestyle": lifestyle,
        "pain_index": pain_index,
        "purchase_power": purchase_power,
        "brand_familiarity": brand_familiarity,
    }


def _top_metros(db: Session, upload_id: str | None, states: list[str] | None, skus: list[str], limit: int = 5) -> list[dict]:
    from app.campaign.dashboards import get_metro_intelligence_dashboard

    payload = get_metro_intelligence_dashboard(db, upload_id, None)
    metros = payload.get("metros") or []
    state_set = set(states or [])
    if state_set:
        metros = [m for m in metros if state_set.intersection(set(m.get("states") or []))]

    sku_ratio = 1.0
    if skus:
        db_q = _apply_skus(_base_query(db, upload_id), skus)
        all_customers = int(db_q.with_entities(func.count(Customer.customer_id)).scalar() or 0)
        total_customers = int(_base_query(db, upload_id).with_entities(func.count(Customer.customer_id)).scalar() or 1)
        sku_ratio = all_customers / total_customers if total_customers else 1.0

    ranked = []
    for metro in metros:
        customers = int(round((metro.get("target_customers") or 0) * sku_ratio))
        revenue = round(float(metro.get("expected_revenue") or 0) * sku_ratio, 2)
        if customers <= 0:
            continue
        ranked.append(
            {
                "cbsa_code": metro.get("cbsa_code"),
                "cbsa_name": metro.get("cbsa_name"),
                "states": metro.get("states") or [],
                "customers": customers,
                "revenue": revenue,
                "orders": round(float(metro.get("expected_orders") or 0) * sku_ratio, 2),
                "conversion": float(metro.get("conversion") or 0),
                "opportunity_score": float(metro.get("opportunity_score") or 0),
                "asian_relative_index": (metro.get("demographics") or {}).get("asian_relative_index"),
            }
        )
    ranked.sort(key=lambda row: row["revenue"], reverse=True)
    return ranked[:limit]


def _simulate_cache_key(
    upload_id: str | None,
    *,
    main_sku: str,
    additional_skus: list[str] | None,
    states: list[str] | None,
    segment_filters: dict | None,
) -> str:
    payload = {
        "upload_id": upload_id,
        "main_sku": main_sku,
        "additional_skus": sorted(additional_skus or []),
        "states": sorted(states or []),
        "segment_filters": segment_filters or {},
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _run_simulation(
    db: Session,
    upload_id: str | None,
    *,
    main_sku: str,
    additional_skus: list[str] | None = None,
    states: list[str] | None = None,
    segment_filters: dict | None = None,
) -> dict:
    skus = []
    if main_sku:
        skus.append(main_sku.strip())
    for sku in additional_skus or []:
        code = (sku or "").strip()
        if code and code not in skus:
            skus.append(code)
    if not skus:
        raise ValueError("main_sku is required")

    base = _base_query(db, upload_id)
    db_scope = _apply_skus(base, skus)
    phase1 = _apply_states(db_scope, states)
    phase2 = _apply_segment_filters(phase1, segment_filters)

    by_sku = (
        db_scope.with_entities(
            CustomerIntelligence.recommended_product,
            func.count(Customer.customer_id),
            func.coalesce(func.sum(CustomerIntelligence.expected_revenue), 0.0),
        )
        .group_by(CustomerIntelligence.recommended_product)
        .all()
    )

    return {
        "skus": skus,
        "main_sku": main_sku,
        "db_potential": _aggregate_kpis(db_scope),
        "by_sku": [
            {
                "product": product,
                "customers": int(customers or 0),
                "revenue": round(float(revenue or 0), 2),
            }
            for product, customers, revenue in by_sku
        ],
        "phase1": {
            "kpis": _aggregate_kpis(phase1),
            "by_state": _by_state(phase1),
            "sku_by_state": _by_state(db_scope),
            "top_metros": _top_metros(db, upload_id, states, skus, limit=5),
        },
        "phase2": {
            "kpis": _aggregate_kpis(phase2),
            # Keep segment distributions on Phase 1 scope so legend/chart layout stays stable while KPIs refine.
            "segment_distributions": _segment_distributions(phase1),
        },
    }


def simulate_email_campaign_opportunity(
    db: Session,
    upload_id: str | None,
    *,
    main_sku: str,
    additional_skus: list[str] | None = None,
    states: list[str] | None = None,
    segment_filters: dict | None = None,
) -> dict:
    if not settings.opportunity_simulate_cache_enabled:
        return _run_simulation(
            db,
            upload_id,
            main_sku=main_sku,
            additional_skus=additional_skus,
            states=states,
            segment_filters=segment_filters,
        )

    cache_key = _simulate_cache_key(
        upload_id,
        main_sku=main_sku,
        additional_skus=additional_skus,
        states=states,
        segment_filters=segment_filters,
    )
    now = time.time()
    ttl = max(30, int(settings.opportunity_simulate_cache_ttl_seconds))

    with _SIMULATE_CACHE_LOCK:
        hit = _SIMULATE_CACHE.get(cache_key)
        if hit and now - hit[0] < ttl:
            return hit[1]

    result = _run_simulation(
        db,
        upload_id,
        main_sku=main_sku,
        additional_skus=additional_skus,
        states=states,
        segment_filters=segment_filters,
    )

    with _SIMULATE_CACHE_LOCK:
        _SIMULATE_CACHE[cache_key] = (now, result)
        if len(_SIMULATE_CACHE) > 128:
            expired = [key for key, (ts, _) in _SIMULATE_CACHE.items() if now - ts >= ttl]
            for key in expired:
                _SIMULATE_CACHE.pop(key, None)

    return result
