"""Executive Dashboard — live aggregates from uploaded customer intelligence."""

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import and_, case, func, literal, text
from sqlalchemy.orm import Session

from app.campaign.opportunity_score import (
    apply_radar_axis_spreads,
    compute_state_opportunity_score,
    compute_zip_opportunity_score,
    product_series_code,
    recommendation_products_for_ceragem_segment,
    recommendation_products_for_purchase_power_band,
)
from app.intelligence.ceragem_rules import ceragem_segment_sort_key
from app.geo.brand_familiarity_geo import KOREAN_STATE_HIGH_POPULATION
from app.geo.geo_market_signals import STATE_BRAND_AFFINITY, brand_geo_boost, customer_brand_enclave_match, metro_tier
from app.intelligence.forecasting import le_frame_incentive
from app.acquisition.rollup import ROLLUP_KEY_SEP, has_distribution_rollups
from app.cache.dashboard_cache import (
    cached_dashboard,
    dashboard_cache_generation,
    DASHBOARD_BUILD_VERSION,
    register_dashboard_cache_hook,
)
from app.commercial.catalog import get_runtime_version
from app.commercial.summary import build_commercial_intelligence_summary
from app.models.audit import AuditLog
from app.models.campaign import Campaign, CampaignState
from app.models.customer import Customer, CustomerDatalogix, CustomerIntelligence
from app.models.zip import ZipIntelligence
from app.models.raw import RawUpload
from app.models.scale import UploadRollup
from app.models.v16_schema import UploadHistory
from app.reference.chronic_pain_geo import state_chronic_pain_score, state_chronic_pain_tier
from app.reference.registry import ACTIVE_PRODUCT_CODES, COMMERCIAL_VERSION, PRODUCT_CATALOG
from app.schema.mv_reads import read_mv_product_performance, read_mv_state_revenue
from app.utils.timezone import format_app_date, format_app_datetime

_INDEX_LEVEL_VALUES = {"High": 0.875, "Medium": 0.6, "Low": 0.25}

_LOOKUP_CACHE: dict[str, object] = {}


def _lookup_cache_key(upload_id: uuid.UUID | None, name: str) -> str:
    uid = str(upload_id) if upload_id else "all"
    return f"{dashboard_cache_generation()}:{uid}:{name}"


def _cached_lookup(upload_id: uuid.UUID | None, name: str, factory):
    key = _lookup_cache_key(upload_id, name)
    hit = _LOOKUP_CACHE.get(key)
    if hit is not None:
        return hit
    value = factory()
    _LOOKUP_CACHE[key] = value
    return value


def _clear_executive_lookup_cache() -> None:
    _LOOKUP_CACHE.clear()


register_dashboard_cache_hook(_clear_executive_lookup_cache)


def _parse_rollup_payload(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}

_DISCONTINUED_PRODUCT_REMAP = {
    p["code"]: "Pause M6"
    for p in PRODUCT_CATALOG
    if not p.get("active", True) and p["family"] in {"Master", "Pause"}
}
_LEGACY_PRODUCT_REMAP = {
    "Pause M2": "Pause M6",
    "MediSpa / Cellunic": "Master S4",
    "Pause S4": "Master S4",
    "Master V4": "Master S4",
}


def _normalize_active_product(product: str | None) -> str:
    code = (product or "Unknown").strip()
    if code in ACTIVE_PRODUCT_CODES:
        return code
    if code in _LEGACY_PRODUCT_REMAP:
        return _LEGACY_PRODUCT_REMAP[code]
    return _DISCONTINUED_PRODUCT_REMAP.get(code, "Pause M6")


def _rollup_weighted_index(db: Session, dimension: str, upload_id: uuid.UUID | None) -> float:
    q = (
        db.query(UploadRollup.key, func.sum(UploadRollup.customer_count))
        .filter(UploadRollup.dimension == dimension)
    )
    if upload_id:
        q = q.filter(UploadRollup.upload_id == upload_id)
    rows = q.group_by(UploadRollup.key).all()
    total = sum(int(count or 0) for _, count in rows)
    if not total:
        return 0.0
    weighted = sum(_INDEX_LEVEL_VALUES.get(str(key or "Low"), 0.25) * int(count or 0) for key, count in rows)
    return round(weighted / total, 4)


def _rollup_kpis(db: Session, upload_id: uuid.UUID | None) -> dict | None:
    state_q = (
        db.query(
            func.sum(UploadRollup.customer_count),
            func.sum(UploadRollup.expected_orders),
            func.sum(UploadRollup.expected_revenue),
        )
        .filter(UploadRollup.dimension == "state", UploadRollup.scope == "*")
    )
    if upload_id:
        state_q = state_q.filter(UploadRollup.upload_id == upload_id)
    count, orders, revenue = state_q.one()
    rollup_customers = int(count or 0)
    if rollup_customers == 0:
        return None

    total = rollup_customers
    targetable = rollup_customers
    if upload_id:
        targetable = int(
            db.query(func.count(Customer.customer_id))
            .filter(Customer.upload_id == upload_id, Customer.email.isnot(None))
            .scalar()
            or rollup_customers
        )

    since = datetime.utcnow() - timedelta(days=30)
    if upload_id:
        new_customers = total
    else:
        new_customers = int(
            db.query(func.count(Customer.customer_id)).filter(Customer.created_at >= since).scalar() or 0
        )

    email_brand_q = None
    cp_q = None
    if upload_id:
        email_brand_q = (
            db.query(
                func.avg(CustomerIntelligence.email_response_index),
                func.avg(CustomerIntelligence.brand_familiarity_index),
            )
            .select_from(CustomerIntelligence)
            .join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
            .filter(Customer.upload_id == upload_id)
        )
        cp_q = (
            db.query(func.avg(CustomerIntelligence.campaign_priority))
            .join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
            .filter(Customer.upload_id == upload_id)
        )
    avg_email = avg_brand = avg_cp = 0.0
    if email_brand_q is not None:
        avg_email, avg_brand = email_brand_q.one()
    if cp_q is not None:
        avg_cp = float(cp_q.scalar() or 0)
    expected_orders = float(orders or 0)
    expected_revenue = float(revenue or 0)

    return {
        "total_customers": total,
        "targetable_customers": targetable,
        "new_customers": new_customers,
        "expected_conversion": round(expected_orders, 2),
        "expected_revenue": round(expected_revenue, 2),
        "expected_orders": round(expected_orders, 2),
        "conversion_rate": round(expected_orders / max(total, 1), 6),
        "predicted_conversion_rate": round(expected_orders / max(total, 1), 6),
        "le_frame_incentive": round(le_frame_incentive(expected_revenue), 2),
        "average_indices": {
            "purchase_power_index": _rollup_weighted_index(db, "purchase_power", upload_id),
            "pain_index": _rollup_weighted_index(db, "pain", upload_id),
            "lifestyle_index": _rollup_weighted_index(db, "lifestyle", upload_id),
            "email_response_index": round(float(avg_email or 0), 4),
            "brand_familiarity_index": round(float(avg_brand or 0), 4),
            "campaign_priority": round(avg_cp, 4),
        },
    }


def _parse_upload_id(upload_id: str | None) -> uuid.UUID | None:
    if not upload_id:
        return None
    return uuid.UUID(upload_id)


def _scoped_customer_query(db: Session, upload_id: uuid.UUID | None):
    q = db.query(Customer)
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    return q


def _intelligence_join(db: Session, upload_id: uuid.UUID | None):
    q = db.query(CustomerIntelligence).join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    return q


def _aggregate_kpis(db: Session, upload_id: uuid.UUID | None) -> dict:
    rollup_kpis = _rollup_kpis(db, upload_id)
    if rollup_kpis:
        return rollup_kpis

    total = _scoped_customer_query(db, upload_id).count()
    targetable = _scoped_customer_query(db, upload_id).filter(Customer.email.isnot(None)).count()

    totals = (
        db.query(
            func.sum(CustomerIntelligence.expected_conversion),
            func.sum(CustomerIntelligence.expected_revenue),
            func.avg(CustomerIntelligence.purchase_power_index),
            func.avg(CustomerIntelligence.pain_index),
            func.avg(CustomerIntelligence.lifestyle_index),
            func.avg(CustomerIntelligence.email_response_index),
            func.avg(CustomerIntelligence.brand_familiarity_index),
            func.avg(CustomerIntelligence.campaign_priority),
            func.avg(CustomerIntelligence.baseline_conversion),
            func.avg(CustomerIntelligence.promo_uplift),
        )
        .select_from(CustomerIntelligence)
        .join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
    )
    if upload_id:
        totals = totals.filter(Customer.upload_id == upload_id)
    row = totals.one()

    expected_orders = float(row[0] or 0)
    expected_revenue = float(row[1] or 0)
    conversion = expected_orders / total if total else 0.0

    new_customers = total
    if upload_id:
        new_customers = total
    else:
        since = datetime.utcnow() - timedelta(days=30)
        new_customers = (
            _scoped_customer_query(db, None).filter(Customer.created_at >= since).count()
        )

    return {
        "total_customers": total,
        "targetable_customers": targetable,
        "new_customers": new_customers,
        "expected_conversion": round(expected_orders, 2),
        "expected_revenue": round(expected_revenue, 2),
        "expected_orders": round(expected_orders, 2),
        "conversion_rate": round(conversion, 6),
        "predicted_conversion_rate": round(conversion, 6),
        "baseline_conversion_rate": round(float(row[8] or 0), 6),
        "promo_uplift_rate": round(float(row[9] or 0), 6),
        "le_frame_incentive": round(le_frame_incentive(expected_revenue), 2),
        "average_indices": {
            "purchase_power_index": round(float(row[2] or 0), 4),
            "pain_index": round(float(row[3] or 0), 4),
            "lifestyle_index": round(float(row[4] or 0), 4),
            "email_response_index": round(float(row[5] or 0), 4),
            "brand_familiarity_index": round(float(row[6] or 0), 4),
            "campaign_priority": round(float(row[7] or 0), 4),
        },
    }


def _revenue_by_state(db: Session, upload_id: uuid.UUID | None) -> list[dict]:
    if upload_id:
        rollups = (
            db.query(UploadRollup)
            .filter(UploadRollup.upload_id == upload_id, UploadRollup.dimension == "state", UploadRollup.scope == "*")
            .all()
        )
        if rollups:
            return [
                {
                    "state": r.key,
                    "revenue": round(float(r.expected_revenue or 0), 2),
                    "orders": round(float(r.expected_orders or 0), 2),
                    "customers": int(r.customer_count or 0),
                    "conversion": round(float(r.expected_orders or 0) / max(int(r.customer_count or 0), 1), 4),
                }
                for r in sorted(rollups, key=lambda x: -(x.expected_revenue or 0))
            ]
        upload = db.query(RawUpload).filter(RawUpload.upload_id == upload_id).first()
        if upload and upload.status in {"failed", "pending"}:
            return []
    else:
        rollups = (
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
        if rollups:
            result = []
            for state, count, orders, revenue in rollups:
                count_i = int(count or 0)
                orders_f = float(orders or 0)
                result.append(
                    {
                        "state": state or "Unknown",
                        "revenue": round(float(revenue or 0), 2),
                        "orders": round(orders_f, 2),
                        "customers": count_i,
                        "conversion": round(orders_f / max(count_i, 1), 4),
                    }
                )
            return sorted(result, key=lambda x: -x["revenue"])

        mv_rows = read_mv_state_revenue(db) if upload_id is None else None
        if mv_rows:
            return mv_rows

    rows = (
        db.query(
            Customer.state,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_conversion),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if upload_id:
        rows = rows.filter(Customer.upload_id == upload_id)
    rows = rows.group_by(Customer.state).all()

    result = []
    for state, count, orders, revenue in rows:
        count_i = int(count or 0)
        orders_f = float(orders or 0)
        result.append(
            {
                "state": state or "Unknown",
                "revenue": round(float(revenue or 0), 2),
                "orders": round(orders_f, 2),
                "customers": count_i,
                "conversion": round(orders_f / max(count_i, 1), 4),
            }
        )
    return sorted(result, key=lambda x: -x["revenue"])


def _index_pct(value: float | None) -> float:
    if value is None:
        return 0.0
    return round(min(100.0, max(0.0, float(value) * 100)), 1)


def _index_level_from_float(value: float | None) -> str:
    if value is None:
        return "Low"
    if float(value) >= 0.75:
        return "High"
    if float(value) >= 0.45:
        return "Medium"
    return "Low"


# Recent Opportunities — nationwide intelligence-ranked ZIPs (not revenue-only TX bias).
RECENT_OPPORTUNITIES_ZIP_LIMIT = 6
RECENT_OPPORTUNITIES_MIN_ZIP_CUSTOMERS = 30
RECENT_OPPORTUNITIES_MAX_PER_STATE = 1
RECENT_OPPORTUNITIES_TARGET_SERIES = ("V", "M", "S")


def _product_series_code(product: str | None) -> str:
    code = (product or "").strip()
    if code.startswith("Master V"):
        return "V"
    if code.startswith("Pause M"):
        return "M"
    if code.startswith("Pause S"):
        return "S"
    return "Other"


def _state_purchase_power_geo_by_state(db: Session, upload_id: uuid.UUID | None) -> dict[str, dict[str, float | str]]:
    """
    Geo-weighted Purchase Power for Opportunity Radar spread.

    Tiers (ORION Section 15 + ZIP Rules 021–022):
    - High Income Geography: top-quartile state/ZIP median income or >=35% premium (top-50) ZIP customers
    - Lower Income Geography: bottom-quartile state income and <12% premium ZIP customers
    - Mid Income Geography: all other states/ZIPs
    """

    q = (
        db.query(
            Customer.state,
            func.avg(CustomerIntelligence.purchase_power_index),
            func.avg(ZipIntelligence.median_income),
            func.sum(case((ZipIntelligence.top50_rank.is_(True), 1), else_=0)),
            func.count(Customer.customer_id),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .outerjoin(ZipIntelligence, Customer.zip == ZipIntelligence.zip)
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    rows = q.group_by(Customer.state).all()

    state_stats: list[dict] = []
    for state, pp_avg, median_income_avg, premium_count, total in rows:
        total_i = int(total or 0)
        income = float(median_income_avg) if median_income_avg is not None else None
        state_stats.append(
            {
                "state": state or "Unknown",
                "pp_avg": float(pp_avg or 0),
                "income": income,
                "premium_pct": int(premium_count or 0) / max(total_i, 1),
            }
        )

    incomes = sorted(s["income"] for s in state_stats if s["income"] is not None)
    if not incomes:
        return {
            s["state"]: {
                "purchase_power_score": _index_pct(s["pp_avg"]),
                "purchase_power_tier": "Mid Income Geography",
            }
            for s in state_stats
        }

    high_income_threshold = incomes[max(0, int(len(incomes) * 0.75) - 1)]
    low_income_threshold = incomes[min(len(incomes) - 1, int(len(incomes) * 0.25))]

    def income_percentile(income: float | None) -> float:
        if income is None:
            return 0.5
        if len(incomes) == 1:
            return 0.5
        below = sum(1 for value in incomes if value < income)
        return below / (len(incomes) - 1)

    result: dict[str, dict[str, float | str]] = {}
    for s in state_stats:
        income_pct = income_percentile(s["income"])
        premium_pct = s["premium_pct"]
        base = _index_pct(s["pp_avg"])

        is_high = (s["income"] is not None and s["income"] >= high_income_threshold) or premium_pct >= 0.35
        is_low = (
            s["income"] is not None
            and s["income"] <= low_income_threshold
            and premium_pct < 0.12
        )

        if is_high:
            tier = "High Income Geography"
            geo = 68 + min(28, income_pct * 18 + premium_pct * 48)
        elif is_low:
            tier = "Lower Income Geography"
            geo = 6 + min(28, income_pct * 24)
        else:
            tier = "Mid Income Geography"
            geo = 30 + max(0.0, income_pct - 0.18) * 50

        geo = round(min(96.0, max(4.0, geo)), 1)
        weighted = round(0.28 * base + 0.72 * geo, 1)

        result[s["state"]] = {
            "purchase_power_score": weighted,
            "purchase_power_tier": tier,
            "purchase_power_geo_score": geo,
        }

    return result


# Primary Korean/Asian metro label for radar tier display (Brand Familiarity v4).
STATE_PRIMARY_BRAND_METRO: dict[str, str] = {
    "TX": "Houston metro (TX Korean corridor)",
    "CA": "Los Angeles metro",
    "NY": "New York / NJ metro",
    "NJ": "New York / NJ metro",
    "WA": "Seattle metro",
    "IL": "Chicago metro",
    "GA": "Atlanta metro",
    "PA": "Philadelphia metro",
    "VA": "Washington DC metro",
    "MD": "Washington DC metro",
    "DC": "Washington DC metro",
    "HI": "Honolulu / Asian density",
}


STATE_REPRESENTATIVE_CITY: dict[str, str] = {
    "TX": "Houston",
    "CA": "Los Angeles",
    "NY": "New York",
    "NJ": "Palisades Park",
    "WA": "Seattle",
    "IL": "Chicago",
    "GA": "Atlanta",
    "PA": "Philadelphia",
    "VA": "Annandale",
    "MD": "Bethesda",
    "DC": "Washington",
    "HI": "Honolulu",
}


def _brand_familiarity_tier_label(state: str, *, enclave_pct: float, avg_geo_boost: float) -> str:
    primary_metro = STATE_PRIMARY_BRAND_METRO.get(state, "")
    if primary_metro and state in KOREAN_STATE_HIGH_POPULATION and avg_geo_boost >= 0.14:
        return f"Korean Metro · {primary_metro}"
    if avg_geo_boost >= 0.22:
        return f"Asian Density Tier-1 ({state})"
    if avg_geo_boost >= 0.14:
        return f"Asian Density Tier-2 ({state})"
    if state in KOREAN_STATE_HIGH_POPULATION:
        return f"Korean Population State ({state})"
    if state in STATE_BRAND_AFFINITY:
        return f"Asian Brand Corridor ({state})"
    if enclave_pct >= 0.08:
        return f"Brand Enclave Geography ({state})"
    return "Standard Geography"


def _state_brand_familiarity_geo_by_state(db: Session, upload_id: uuid.UUID | None) -> dict[str, dict[str, float | str]]:
    """
    Geo-weighted Brand Familiarity v4 for Opportunity Radar.

    Customer brand_familiarity_index already blends v4 geo boosts; this layer adds
    state-level tier labels across CA/NJ/NY/GA/WA/VA/IL/MD/HI — not only TX/PA.
    """

    q = (
        db.query(
            Customer.state,
            func.avg(CustomerIntelligence.brand_familiarity_index),
            func.count(Customer.customer_id),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    rows = q.group_by(Customer.state).all()

    result: dict[str, dict[str, float | str]] = {}
    for state, brand_avg, total in rows:
        key = state or "Unknown"
        base_pct = _index_pct(float(brand_avg or 0))

        rep_city = STATE_REPRESENTATIVE_CITY.get(key)
        signals = brand_geo_boost(zip_code=None, state=key, city=rep_city)
        avg_geo_boost = float(signals.get("brand_geo_boost") or 0)

        enclave_match = customer_brand_enclave_match(zip_code=None, state=key, city=rep_city)
        enclave_pct = 1.0 if enclave_match else 0.0

        tier = _brand_familiarity_tier_label(key, enclave_pct=enclave_pct, avg_geo_boost=avg_geo_boost)
        if signals.get("korean_metro_match"):
            tier = f"Korean Metro · {signals.get('korean_metro_label') or STATE_PRIMARY_BRAND_METRO.get(key, rep_city or key)}"
        elif signals.get("asian_city_match"):
            tier = f"Asian Density · {rep_city or key} ({signals.get('asian_city_tier', 'tier')})"

        geo = 14 + (avg_geo_boost / 0.45) * 62 + (8 if enclave_match else 0)
        geo = round(min(96.0, max(10.0, geo)), 1)
        weighted = round(0.40 * base_pct + 0.60 * geo, 1)

        result[key] = {
            "brand_score": weighted,
            "brand_familiarity_tier": tier,
            "brand_familiarity_geo_score": geo,
            "brand_enclave_pct": round(enclave_pct * 100, 1),
            "brand_geo_boost_avg": round(avg_geo_boost, 4),
        }

    return result


def _state_lifestyle_geo_by_state(db: Session, upload_id: uuid.UUID | None) -> dict[str, dict[str, float | str]]:
    """
    Geo-weighted Lifestyle for Opportunity Radar spread.

    Layers wellness segment concentration, Pause M Series (sleep/rest) share,
    premium ZIP affluence, and inverse pain moderation (wellness vs clinical markets).
    """

    q = (
        db.query(
            Customer.state,
            func.avg(CustomerIntelligence.lifestyle_index),
            func.avg(CustomerIntelligence.pain_index),
            func.sum(case((CustomerIntelligence.ceragem_segment.like("%Wellness%"), 1), else_=0)),
            func.sum(case((CustomerIntelligence.recommended_product.like("Pause M%"), 1), else_=0)),
            func.sum(case((ZipIntelligence.top50_rank.is_(True), 1), else_=0)),
            func.count(Customer.customer_id),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .outerjoin(ZipIntelligence, Customer.zip == ZipIntelligence.zip)
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    rows = q.group_by(Customer.state).all()

    result: dict[str, dict[str, float | str]] = {}
    for state, lifestyle_avg, pain_avg, wellness_count, m_series_count, premium_count, total in rows:
        key = state or "Unknown"
        total_i = max(int(total or 0), 1)
        wellness_pct = int(wellness_count or 0) / total_i
        m_series_pct = int(m_series_count or 0) / total_i
        premium_pct = int(premium_count or 0) / total_i
        base = _index_pct(float(lifestyle_avg or 0))
        pain_pct = _index_pct(float(pain_avg or 0))
        pain_relief = max(0.0, (52.0 - pain_pct) / 52.0)

        if wellness_pct >= 0.32 and premium_pct >= 0.18:
            tier = "Premium Wellness Geography"
            geo = 62 + min(32, wellness_pct * 55 + premium_pct * 40 + pain_relief * 18)
        elif wellness_pct >= 0.22 or m_series_pct >= 0.28:
            tier = "Lifestyle Wellness Geography"
            geo = 44 + min(38, wellness_pct * 48 + m_series_pct * 35 + pain_relief * 14)
        elif pain_pct >= 48:
            tier = "Therapeutic / Pain Geography"
            geo = 14 + min(28, pain_pct * 0.45)
        else:
            tier = "Standard Lifestyle Geography"
            geo = 26 + min(34, wellness_pct * 40 + m_series_pct * 22 + pain_relief * 20)

        geo = round(min(96.0, max(6.0, geo)), 1)
        weighted = round(0.30 * base + 0.70 * geo, 1)

        result[key] = {
            "lifestyle_score": weighted,
            "lifestyle_tier": tier,
            "lifestyle_geo_score": geo,
            "wellness_segment_pct": round(wellness_pct * 100, 1),
            "m_series_pct": round(m_series_pct * 100, 1),
        }

    return result


def _state_digital_engagement_geo_by_state(db: Session, upload_id: uuid.UUID | None) -> dict[str, dict[str, float | str]]:
    """
    Geo-weighted Digital Engagement for Opportunity Radar spread.

    Uses one state-level aggregate (not per-ZIP) plus representative metro tier for speed.
    """

    q = (
        db.query(
            Customer.state,
            func.avg(CustomerIntelligence.email_response_index),
            func.count(Customer.customer_id),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    rows = q.group_by(Customer.state).all()

    result: dict[str, dict[str, float | str]] = {}
    for state, digital_avg, total in rows:
        key = state or "Unknown"
        base_pct = _index_pct(float(digital_avg or 0))
        rep_city = STATE_REPRESENTATIVE_CITY.get(key)
        metro_signal = metro_tier(zip_code=None, state=key, city=rep_city)

        if metro_signal == "tier1":
            tier1_pct, tier2_pct, metro_pct = 0.12, 0.08, 0.20
            tier = "Tier-1 Metro Commerce"
            geo = 66 + min(30, tier1_pct * 140 + tier2_pct * 45)
        elif metro_signal == "tier2":
            tier1_pct, tier2_pct, metro_pct = 0.04, 0.14, 0.18
            tier = "Tier-2 Metro Commerce"
            geo = 48 + min(32, tier2_pct * 95 + tier1_pct * 70)
        elif metro_signal in (None, "rural", "low"):
            tier1_pct, tier2_pct, metro_pct = 0.01, 0.03, 0.04
            tier = "Lower Digital Geography"
            geo = 12 + min(22, metro_pct * 90)
        else:
            tier1_pct, tier2_pct, metro_pct = 0.03, 0.08, 0.11
            tier = "Mid Digital Geography"
            geo = 34 + min(28, metro_pct * 70)

        geo = round(min(96.0, max(8.0, geo)), 1)
        weighted = round(0.30 * base_pct + 0.70 * geo, 1)

        result[key] = {
            "digital_score": weighted,
            "digital_engagement_tier": tier,
            "digital_engagement_geo_score": geo,
            "digital_metro_pct": round(metro_pct * 100, 1),
        }

    return result


def _compute_state_geo_bundle_by_state(db: Session, upload_id: uuid.UUID | None) -> dict[str, dict[str, float | str]]:
    """Single-pass state aggregates for Radar intel + PP + Lifestyle + Brand geo layers."""

    q = (
        db.query(
            Customer.state,
            func.avg(CustomerIntelligence.lifestyle_index),
            func.avg(CustomerIntelligence.purchase_power_index),
            func.avg(CustomerIntelligence.pain_index),
            func.avg(CustomerIntelligence.email_response_index),
            func.avg(CustomerIntelligence.brand_familiarity_index),
            func.avg(ZipIntelligence.median_income),
            func.sum(case((ZipIntelligence.top50_rank.is_(True), 1), else_=0)),
            func.sum(case((CustomerIntelligence.ceragem_segment.like("%Wellness%"), 1), else_=0)),
            func.sum(case((CustomerIntelligence.recommended_product.like("Pause M%"), 1), else_=0)),
            func.count(Customer.customer_id),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .outerjoin(ZipIntelligence, Customer.zip == ZipIntelligence.zip)
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    rows = q.group_by(Customer.state).all()

    state_stats: list[dict] = []
    for (
        state,
        lifestyle_avg,
        pp_avg,
        pain_avg,
        digital_avg,
        brand_avg,
        median_income_avg,
        premium_count,
        wellness_count,
        m_series_count,
        total,
    ) in rows:
        key = state or "Unknown"
        total_i = int(total or 0)
        income = float(median_income_avg) if median_income_avg is not None else None
        state_stats.append(
            {
                "state": key,
                "lifestyle_avg": float(lifestyle_avg or 0),
                "pp_avg": float(pp_avg or 0),
                "pain_avg": float(pain_avg or 0),
                "digital_avg": float(digital_avg or 0),
                "brand_avg": float(brand_avg or 0),
                "income": income,
                "premium_pct": int(premium_count or 0) / max(total_i, 1),
                "wellness_pct": int(wellness_count or 0) / max(total_i, 1),
                "m_series_pct": int(m_series_count or 0) / max(total_i, 1),
                "total": total_i,
            }
        )

    incomes = sorted(s["income"] for s in state_stats if s["income"] is not None)
    high_income_threshold = incomes[max(0, int(len(incomes) * 0.75) - 1)] if incomes else None
    low_income_threshold = incomes[min(len(incomes) - 1, int(len(incomes) * 0.25))] if incomes else None

    def income_percentile(income: float | None) -> float:
        if income is None or not incomes:
            return 0.5
        if len(incomes) == 1:
            return 0.5
        below = sum(1 for value in incomes if value < income)
        return below / (len(incomes) - 1)

    bundle: dict[str, dict[str, float | str]] = {}
    for s in state_stats:
        key = s["state"]
        lifestyle_pct = _index_pct(s["lifestyle_avg"])
        pain_pct = _index_pct(s["pain_avg"])
        pp_base = _index_pct(s["pp_avg"])
        brand_base = _index_pct(s["brand_avg"])

        income_pct = income_percentile(s["income"])
        premium_pct = s["premium_pct"]
        is_high = (s["income"] is not None and high_income_threshold is not None and s["income"] >= high_income_threshold) or premium_pct >= 0.35
        is_low = (
            s["income"] is not None
            and low_income_threshold is not None
            and s["income"] <= low_income_threshold
            and premium_pct < 0.12
        )
        if is_high:
            pp_tier = "High Income Geography"
            pp_geo = 68 + min(28, income_pct * 18 + premium_pct * 48)
        elif is_low:
            pp_tier = "Lower Income Geography"
            pp_geo = 6 + min(28, income_pct * 24)
        else:
            pp_tier = "Mid Income Geography"
            pp_geo = 30 + max(0.0, income_pct - 0.18) * 50
        pp_geo = round(min(96.0, max(4.0, pp_geo)), 1)

        wellness_pct = s["wellness_pct"]
        m_series_pct = s["m_series_pct"]
        pain_relief = max(0.0, (52.0 - pain_pct) / 52.0)
        if wellness_pct >= 0.32 and premium_pct >= 0.18:
            lifestyle_tier = "Premium Wellness Geography"
            lifestyle_geo = 62 + min(32, wellness_pct * 55 + premium_pct * 40 + pain_relief * 18)
        elif wellness_pct >= 0.22 or m_series_pct >= 0.28:
            lifestyle_tier = "Lifestyle Wellness Geography"
            lifestyle_geo = 44 + min(38, wellness_pct * 48 + m_series_pct * 35 + pain_relief * 14)
        elif pain_pct >= 48:
            lifestyle_tier = "Therapeutic / Pain Geography"
            lifestyle_geo = 14 + min(28, pain_pct * 0.45)
        else:
            lifestyle_tier = "Standard Lifestyle Geography"
            lifestyle_geo = 26 + min(34, wellness_pct * 40 + m_series_pct * 22 + pain_relief * 20)
        lifestyle_geo = round(min(96.0, max(6.0, lifestyle_geo)), 1)

        rep_city = STATE_REPRESENTATIVE_CITY.get(key)
        signals = brand_geo_boost(zip_code=None, state=key, city=rep_city)
        avg_geo_boost = float(signals.get("brand_geo_boost") or 0)
        enclave_match = customer_brand_enclave_match(zip_code=None, state=key, city=rep_city)
        enclave_pct = 1.0 if enclave_match else 0.0
        brand_tier = _brand_familiarity_tier_label(key, enclave_pct=enclave_pct, avg_geo_boost=avg_geo_boost)
        if signals.get("korean_metro_match"):
            brand_tier = f"Korean Metro · {signals.get('korean_metro_label') or STATE_PRIMARY_BRAND_METRO.get(key, rep_city or key)}"
        elif signals.get("asian_city_match"):
            brand_tier = f"Asian Density · {rep_city or key} ({signals.get('asian_city_tier', 'tier')})"
        brand_geo = 14 + (avg_geo_boost / 0.45) * 62 + (8 if enclave_match else 0)
        brand_geo = round(min(96.0, max(10.0, brand_geo)), 1)

        digital_base = _index_pct(s["digital_avg"])
        metro_signal = metro_tier(zip_code=None, state=key, city=rep_city)
        if metro_signal == "tier1":
            tier1_pct, tier2_pct, metro_pct = 0.12, 0.08, 0.20
            digital_tier = "Tier-1 Metro Commerce"
            digital_geo = 66 + min(30, tier1_pct * 140 + tier2_pct * 45)
        elif metro_signal == "tier2":
            tier1_pct, tier2_pct, metro_pct = 0.04, 0.14, 0.18
            digital_tier = "Tier-2 Metro Commerce"
            digital_geo = 48 + min(32, tier2_pct * 95 + tier1_pct * 70)
        elif metro_signal in (None, "rural", "low"):
            tier1_pct, tier2_pct, metro_pct = 0.01, 0.03, 0.04
            digital_tier = "Lower Digital Geography"
            digital_geo = 12 + min(22, metro_pct * 90)
        else:
            tier1_pct, tier2_pct, metro_pct = 0.03, 0.08, 0.11
            digital_tier = "Mid Digital Geography"
            digital_geo = 34 + min(28, metro_pct * 70)
        digital_geo = round(min(96.0, max(8.0, digital_geo)), 1)

        pain_geo = state_chronic_pain_score(key)
        pain_tier = state_chronic_pain_tier(key)

        bundle[key] = {
            "lifestyle_score": round(0.30 * lifestyle_pct + 0.70 * lifestyle_geo, 1),
            "lifestyle_tier": lifestyle_tier,
            "lifestyle_geo_score": lifestyle_geo,
            "wellness_segment_pct": round(wellness_pct * 100, 1),
            "m_series_pct": round(m_series_pct * 100, 1),
            "purchase_power_score": round(0.28 * pp_base + 0.72 * pp_geo, 1),
            "purchase_power_tier": pp_tier,
            "purchase_power_geo_score": pp_geo,
            "pain_index_score": round(0.35 * pain_pct + 0.65 * pain_geo, 1),
            "pain_index_tier": pain_tier,
            "pain_index_geo_score": pain_geo,
            "brand_score": round(0.40 * brand_base + 0.60 * brand_geo, 1),
            "brand_familiarity_tier": brand_tier,
            "brand_familiarity_geo_score": brand_geo,
            "brand_enclave_pct": round(enclave_pct * 100, 1),
            "brand_geo_boost_avg": round(avg_geo_boost, 4),
            "purchase_power_index_score": pp_base,
            "digital_score": round(0.30 * digital_base + 0.70 * digital_geo, 1),
            "digital_engagement_tier": digital_tier,
            "digital_engagement_geo_score": digital_geo,
            "digital_metro_pct": round(metro_pct * 100, 1),
        }

    return bundle


def _state_geo_bundle_by_state(db: Session, upload_id: uuid.UUID | None) -> dict[str, dict[str, float | str]]:
    return _cached_lookup(
        upload_id,
        "geo_bundle",
        lambda: _compute_state_geo_bundle_by_state(db, upload_id),
    )


def _state_intelligence_by_state(db: Session, upload_id: uuid.UUID | None) -> dict[str, dict[str, float]]:
    """Per-state average intelligence indices for Opportunity Radar axes."""

    q = (
        db.query(
            Customer.state,
            func.avg(CustomerIntelligence.lifestyle_index),
            func.avg(CustomerIntelligence.purchase_power_index),
            func.avg(CustomerIntelligence.pain_index),
            func.avg(CustomerIntelligence.email_response_index),
            func.avg(CustomerIntelligence.brand_familiarity_index),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    rows = q.group_by(Customer.state).all()
    return {
        (state or "Unknown"): {
            "lifestyle_score": _index_pct(lifestyle),
            "purchase_power_index_score": _index_pct(pp),
            "pain_index_score": _index_pct(pain),
            "digital_score": _index_pct(digital),
            "brand_score": _index_pct(brand),
        }
        for state, lifestyle, pp, pain, digital, brand in rows
    }


RADAR_TOP_STATES_PER_PRODUCT = 10
# Alias — executive dashboard uses shared DASHBOARD_BUILD_VERSION for cache busting.
EXECUTIVE_DASHBOARD_BUILD_VERSION = DASHBOARD_BUILD_VERSION

# Promo SKUs without direct recommendation volume — project demand from adjacent line demand.
from app.campaign.standing_promo_demand import (
    build_standing_promo_opportunity_rows,
    pick_highest_conversion_opportunity,
    standing_promo_outreach_product,
    synthesize_standing_promo_cells,
)


def _product_breakdown_by_states(
    db: Session,
    upload_id: uuid.UUID | None,
    state_codes: list[str],
) -> list[dict]:
    """Per-state product rollups for Opportunity Radar (state × product points)."""
    if not state_codes:
        return []

    if upload_id:
        rows = (
            db.query(
                UploadRollup.scope,
                UploadRollup.key,
                UploadRollup.customer_count,
                UploadRollup.expected_orders,
                UploadRollup.expected_revenue,
            )
            .filter(
                UploadRollup.upload_id == upload_id,
                UploadRollup.dimension == "product",
                UploadRollup.scope.in_(state_codes),
                UploadRollup.key.isnot(None),
                UploadRollup.key != "Unknown",
            )
            .all()
        )
        return [
            {
                "state": scope or "Unknown",
                "product": _normalize_active_product(str(key)),
                "customers": int(count or 0),
                "orders": float(orders or 0),
                "revenue": float(revenue or 0),
            }
            for scope, key, count, orders, revenue in rows
        ]

    rows = (
        db.query(
            UploadRollup.scope,
            UploadRollup.key,
            func.sum(UploadRollup.customer_count),
            func.sum(UploadRollup.expected_orders),
            func.sum(UploadRollup.expected_revenue),
        )
        .filter(
            UploadRollup.dimension == "product",
            UploadRollup.scope.in_(state_codes),
            UploadRollup.key.isnot(None),
            UploadRollup.key != "Unknown",
        )
        .group_by(UploadRollup.scope, UploadRollup.key)
        .all()
    )
    return [
        {
            "state": scope or "Unknown",
            "product": _normalize_active_product(str(key)),
            "customers": int(count or 0),
            "orders": float(orders or 0),
            "revenue": float(revenue or 0),
        }
        for scope, key, count, orders, revenue in rows
    ]


def _build_radar_opportunities(
    db: Session,
    state_rows: list[dict],
    upload_id: uuid.UUID | None,
) -> list[dict]:
    """
    Build state × product opportunity points scoped to Top N states **per product**.

    Uses BD intelligence rollups plus standing-promo donor synthesis for thin SKUs
    (e.g. Pause S4, Pause M6s).
    """
    state_by_code = {row["state"]: row for row in state_rows}
    state_codes = list(state_by_code.keys())
    if not state_codes:
        return []

    from app.intelligence.ladder_opportunity import (
        aggregate_ladder_state_product_rows,
        merge_state_product_cells,
    )

    segments_by_state = _modal_segment_by_state(db, upload_id)
    primary_rows = _product_breakdown_by_states(db, upload_id, state_codes)
    ladder_rows = aggregate_ladder_state_product_rows(db, upload_id, state_codes)
    cells = merge_state_product_cells(primary_rows, ladder_rows)

    if not cells:
        return []

    # Standing-promo SKUs (Pause S4, Pause M6s, etc.) inherit donor demand when direct
    # intelligence volume is thin — same synthesis as Promotion Coverage / standing promos.
    synthesize_standing_promo_cells(cells, state_codes)

    active_products = {p["code"] for p in PRODUCT_CATALOG if p.get("active", True)}
    max_revenue = max(float(row.get("revenue") or 0) for row in cells.values())
    axis_keys = (
        "lifestyle_score",
        "purchase_power_score",
        "purchase_power_index_score",
        "purchase_power_tier",
        "pain_index_score",
        "lifestyle_tier",
        "digital_score",
        "digital_engagement_tier",
        "brand_score",
        "brand_familiarity_tier",
    )

    by_product: dict[str, list[dict]] = defaultdict(list)
    for (state, product), product_row in cells.items():
        if product not in active_products:
            continue

        state_intel = state_by_code.get(state)
        if not state_intel:
            continue

        customers = int(product_row["customers"])
        orders = float(product_row["orders"])
        revenue = float(product_row["revenue"])
        if customers <= 0 or revenue <= 0:
            continue

        conversion = orders / max(customers, 1)
        score_row = {key: state_intel.get(key) for key in axis_keys}
        score_row.update(
            {
                "revenue": revenue,
                "conversion": conversion,
                "top_product": product,
                "lifestyle_tier": state_intel.get("lifestyle_tier"),
                "ceragem_segment": segments_by_state.get(state),
            }
        )
        opportunity_score = compute_state_opportunity_score(score_row, max_revenue=max_revenue)

        by_product[product].append(
            {
                "id": f"{state}-{product}",
                "label": f"{state} · {product}",
                "state": state,
                "product": product,
                "opportunity_score": opportunity_score,
                "lifestyle_score": state_intel.get("lifestyle_score"),
                "purchase_power_score": state_intel.get("purchase_power_score")
                or state_intel.get("purchase_power_index_score"),
                "purchase_power_tier": state_intel.get("purchase_power_tier"),
                "pain_index_score": state_intel.get("pain_index_score"),
                "lifestyle_tier": state_intel.get("lifestyle_tier"),
                "digital_score": state_intel.get("digital_score"),
                "digital_engagement_tier": state_intel.get("digital_engagement_tier"),
                "brand_score": state_intel.get("brand_score"),
                "brand_familiarity_tier": state_intel.get("brand_familiarity_tier"),
                "customers": customers,
                "revenue": round(revenue, 2),
            }
        )

    opportunities: list[dict] = []
    by_state_donor: dict[str, list[dict]] = defaultdict(list)
    for (state, product), product_row in cells.items():
        by_state_donor[product].append({**product_row, "state": state, "product": product})

    from app.campaign.standing_promo_demand import pad_geo_product_rows

    for product in sorted(by_product.keys()):
        ranked = sorted(by_product[product], key=lambda row: -(float(row.get("opportunity_score") or 0)))
        ranked = pad_geo_product_rows(
            product,
            ranked,
            by_state_donor,
            geo_field="state",
            limit=RADAR_TOP_STATES_PER_PRODUCT,
        )
        opportunities.extend(ranked[:RADAR_TOP_STATES_PER_PRODUCT])

    return sorted(opportunities, key=lambda row: -(float(row.get("opportunity_score") or 0)))


def _modal_segment_from_rollups(db: Session, upload_id: uuid.UUID | None) -> dict[str, str] | None:
    """Pre-aggregated ceragem rollups — avoids a full customer scan for modal segment."""
    if upload_id:
        rows = (
            db.query(
                UploadRollup.scope,
                UploadRollup.key,
                UploadRollup.customer_count,
            )
            .filter(UploadRollup.upload_id == upload_id, UploadRollup.dimension == "ceragem")
            .all()
        )
    else:
        rows = (
            db.query(
                UploadRollup.scope,
                UploadRollup.key,
                func.sum(UploadRollup.customer_count),
            )
            .filter(UploadRollup.dimension == "ceragem")
            .group_by(UploadRollup.scope, UploadRollup.key)
            .all()
        )
    if not rows:
        return None
    best: dict[str, tuple[int, str]] = {}
    for state, segment, count in rows:
        key = state or "Unknown"
        cnt = int(count or 0)
        current = best.get(key)
        label = str(segment or "Mid-Low + Pain Index")
        if current is None or cnt > current[0]:
            best[key] = (cnt, label)
    if len(best) < 10:
        return None
    return {state: segment for state, (_, segment) in best.items()}


def _compute_modal_segment_by_state(db: Session, upload_id: uuid.UUID | None) -> dict[str, str]:
    from_rollups = _modal_segment_from_rollups(db, upload_id)
    if from_rollups:
        return from_rollups

    q = (
        db.query(
            Customer.state.label("state"),
            CustomerIntelligence.ceragem_segment.label("segment"),
            func.count(Customer.customer_id).label("cnt"),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(CustomerIntelligence.ceragem_segment.isnot(None))
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    counts = q.group_by(Customer.state, CustomerIntelligence.ceragem_segment).subquery()
    ranked = (
        db.query(
            counts.c.state,
            counts.c.segment,
            func.row_number()
            .over(partition_by=counts.c.state, order_by=counts.c.cnt.desc())
            .label("rn"),
        )
    ).subquery()
    rows = db.query(ranked.c.state, ranked.c.segment).filter(ranked.c.rn == 1).all()
    return {
        (state or "Unknown"): segment or "Mid-Low + Pain Index"
        for state, segment in rows
    }


def _modal_segment_by_state(db: Session, upload_id: uuid.UUID | None) -> dict[str, str]:
    return _cached_lookup(
        upload_id,
        "modal_segment",
        lambda: _compute_modal_segment_by_state(db, upload_id),
    )


def _pp_bands_from_distribution(score_distribution: list[dict]) -> dict[str, float]:
    for row in score_distribution:
        if row.get("label") == "Purchase Power":
            return {
                "high": float(row.get("high") or 0),
                "medium": float(row.get("medium") or 0),
                "low": float(row.get("low") or 0),
            }
    return {"high": 0.0, "medium": 0.0, "low": 100.0}


PURCHASE_POWER_INCOME_BANDS: tuple[tuple[str, float, float | None], ...] = (
    ("$150K+", 85.0, 0.75),
    ("$100K–$150K", 68.0, 0.60),
    ("$75K–$100K", 52.0, 0.45),
    ("$50K–$75K", 38.0, 0.30),
    ("<$50K", 25.0, None),
)


def _purchase_power_band_case():
    pp = CustomerIntelligence.purchase_power_index
    return case(
        (pp >= 0.75, "$150K+"),
        (pp >= 0.60, "$100K–$150K"),
        (pp >= 0.45, "$75K–$100K"),
        (pp >= 0.30, "$50K–$75K"),
        else_="<$50K",
    )


def _format_purchase_power_distribution_rows(stats_by_band: dict[str, dict]) -> list[dict]:
    total_customers = sum(int(stats["customers"]) for stats in stats_by_band.values())
    denominator = max(total_customers, 1)
    rows: list[dict] = []
    for label, pp_score, _ in PURCHASE_POWER_INCOME_BANDS:
        stats = stats_by_band[label]
        customers = int(stats["customers"])
        top_products = [
            product
            for product, _ in sorted(stats["product_counts"].items(), key=lambda item: -item[1])
        ]
        products = recommendation_products_for_purchase_power_band(pp_score, top_products)
        v_products = [p for p in products if product_series_code(p) == "v"]
        m_products = [p for p in products if product_series_code(p) == "m"]
        ordered_products = v_products + m_products + [p for p in products if product_series_code(p) == "other"]
        rows.append(
            {
                "band": label,
                "customers": customers,
                "pct": round(customers / denominator * 100, 1),
                "revenue": round(float(stats["revenue"]), 2),
                "products": ordered_products[:6],
                "v_series_products": v_products[:2],
                "m_series_products": m_products[:2],
            }
        )
    return rows


def _purchase_power_distribution_from_rollups(db: Session, upload_id: uuid.UUID | None) -> list[dict] | None:
    if not has_distribution_rollups(db, upload_id):
        return None

    if upload_id:
        band_rows = (
            db.query(
                UploadRollup.key,
                UploadRollup.customer_count,
                UploadRollup.expected_revenue,
            )
            .filter(
                UploadRollup.upload_id == upload_id,
                UploadRollup.dimension == "pp_band",
                UploadRollup.scope == "*",
            )
            .all()
        )
        product_rows = (
            db.query(
                UploadRollup.key,
                UploadRollup.customer_count,
            )
            .filter(
                UploadRollup.upload_id == upload_id,
                UploadRollup.dimension == "pp_band_prod",
            )
            .all()
        )
    else:
        band_rows = (
            db.query(
                UploadRollup.key,
                func.sum(UploadRollup.customer_count),
                func.sum(UploadRollup.expected_revenue),
            )
            .filter(UploadRollup.dimension == "pp_band", UploadRollup.scope == "*")
            .group_by(UploadRollup.key)
            .all()
        )
        product_rows = (
            db.query(
                UploadRollup.key,
                func.sum(UploadRollup.customer_count),
            )
            .filter(UploadRollup.dimension == "pp_band_prod")
            .group_by(UploadRollup.key)
            .all()
        )

    if not band_rows:
        return None

    stats_by_band: dict[str, dict] = {
        label: {"customers": 0, "revenue": 0.0, "product_counts": defaultdict(int)}
        for label, _, _ in PURCHASE_POWER_INCOME_BANDS
    }
    for band, customers, revenue in band_rows:
        key = str(band or "<$50K")
        if key not in stats_by_band:
            continue
        stats_by_band[key]["customers"] += int(customers or 0)
        stats_by_band[key]["revenue"] += float(revenue or 0)

    for composite_key, customers in product_rows:
        parts = str(composite_key or "").split(ROLLUP_KEY_SEP, 1)
        if len(parts) != 2:
            continue
        band, product = parts
        key = str(band or "<$50K")
        if key not in stats_by_band:
            continue
        normalized = _normalize_active_product(str(product or ""))
        if normalized and normalized != "Unknown":
            stats_by_band[key]["product_counts"][normalized] += int(customers or 0)

    return _format_purchase_power_distribution_rows(stats_by_band)


def _format_ceragem_distribution_rows(stats_by_segment: dict[str, dict]) -> list[dict]:
    total_customers = sum(int(stats["customers"]) for stats in stats_by_segment.values())
    denominator = max(total_customers, 1)
    rows: list[dict] = []
    for label, stats in sorted(stats_by_segment.items(), key=lambda item: ceragem_segment_sort_key(item[0])):
        customers = int(stats["customers"])
        top_products = [
            product
            for product, _ in sorted(stats["product_counts"].items(), key=lambda item: -item[1])
        ]
        # Keep explicit Ceragem ladder order (do not regroup V-then-M).
        products = recommendation_products_for_ceragem_segment(label, top_products)
        v_products = [p for p in products if product_series_code(p) == "v"]
        m_products = [p for p in products if product_series_code(p) == "m"]
        rows.append(
            {
                "segment": label,
                "customers": customers,
                "pct": round(customers / denominator * 100, 1),
                "revenue": round(float(stats["revenue"]), 2),
                "products": products[:6],
                "v_series_products": v_products[:2],
                "m_series_products": m_products[:2],
            }
        )
    return rows


def _ceragem_distribution_from_rollups(db: Session, upload_id: uuid.UUID | None) -> list[dict] | None:
    if not has_distribution_rollups(db, upload_id):
        return None

    if upload_id:
        segment_rows = (
            db.query(
                UploadRollup.key,
                func.sum(UploadRollup.customer_count),
                func.sum(UploadRollup.expected_revenue),
            )
            .filter(UploadRollup.upload_id == upload_id, UploadRollup.dimension == "ceragem")
            .group_by(UploadRollup.key)
            .all()
        )
        product_rows = (
            db.query(
                UploadRollup.key,
                UploadRollup.customer_count,
            )
            .filter(UploadRollup.upload_id == upload_id, UploadRollup.dimension == "ceragem_prod")
            .all()
        )
    else:
        segment_rows = (
            db.query(
                UploadRollup.key,
                func.sum(UploadRollup.customer_count),
                func.sum(UploadRollup.expected_revenue),
            )
            .filter(UploadRollup.dimension == "ceragem")
            .group_by(UploadRollup.key)
            .all()
        )
        product_rows = (
            db.query(
                UploadRollup.key,
                func.sum(UploadRollup.customer_count),
            )
            .filter(UploadRollup.dimension == "ceragem_prod")
            .group_by(UploadRollup.key)
            .all()
        )

    if not segment_rows:
        return None

    stats_by_segment: dict[str, dict] = {}
    for segment, customers, revenue in segment_rows:
        label = str(segment or "Unknown").strip() or "Unknown"
        stats_by_segment[label] = {
            "customers": int(customers or 0),
            "revenue": float(revenue or 0),
            "product_counts": defaultdict(int),
        }

    for composite_key, customers in product_rows:
        parts = str(composite_key or "").split(ROLLUP_KEY_SEP, 1)
        if len(parts) != 2:
            continue
        segment, product = parts
        label = str(segment or "Unknown").strip() or "Unknown"
        if label not in stats_by_segment:
            continue
        normalized = _normalize_active_product(str(product or ""))
        if normalized and normalized != "Unknown":
            stats_by_segment[label]["product_counts"][normalized] += int(customers or 0)

    return _format_ceragem_distribution_rows(stats_by_segment)


def _purchase_power_distribution(db: Session, upload_id: uuid.UUID | None) -> list[dict]:
    """Income-band customer mix with TAR and sellable SKU list for Mission Control donut hover."""
    from_rollups = _purchase_power_distribution_from_rollups(db, upload_id)
    if from_rollups is not None:
        return from_rollups

    band_case = _purchase_power_band_case()
    q = db.query(CustomerIntelligence).join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)

    stats_by_band: dict[str, dict] = {
        label: {"customers": 0, "revenue": 0.0, "product_counts": defaultdict(int)}
        for label, _, _ in PURCHASE_POWER_INCOME_BANDS
    }
    grouped_rows = (
        q.with_entities(
            band_case.label("band"),
            CustomerIntelligence.recommended_product,
            func.count(CustomerIntelligence.id).label("customers"),
            func.sum(CustomerIntelligence.expected_revenue).label("revenue"),
        )
        .group_by(band_case, CustomerIntelligence.recommended_product)
        .all()
    )
    for band, product, customers, revenue in grouped_rows:
        key = str(band)
        if key not in stats_by_band:
            continue
        count_i = int(customers or 0)
        stats_by_band[key]["customers"] += count_i
        stats_by_band[key]["revenue"] += float(revenue or 0)
        normalized = _normalize_active_product(str(product or ""))
        if normalized and normalized != "Unknown":
            stats_by_band[key]["product_counts"][normalized] += count_i

    return _format_purchase_power_distribution_rows(stats_by_band)


def _ceragem_distribution(db: Session, upload_id: uuid.UUID | None) -> list[dict]:
    """Ceragem Segmentation+ customer mix with TAR and sellable SKU list for Mission Control donut hover."""
    from_rollups = _ceragem_distribution_from_rollups(db, upload_id)
    if from_rollups is not None:
        return from_rollups

    q = db.query(CustomerIntelligence).join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)

    stats_by_segment: dict[str, dict] = {}
    grouped_rows = (
        q.with_entities(
            CustomerIntelligence.ceragem_segment.label("segment"),
            CustomerIntelligence.recommended_product,
            func.count(CustomerIntelligence.id).label("customers"),
            func.sum(CustomerIntelligence.expected_revenue).label("revenue"),
        )
        .filter(CustomerIntelligence.ceragem_segment.isnot(None))
        .group_by(CustomerIntelligence.ceragem_segment, CustomerIntelligence.recommended_product)
        .all()
    )
    for segment, product, customers, revenue in grouped_rows:
        label = str(segment or "Unknown").strip() or "Unknown"
        bucket = stats_by_segment.setdefault(
            label,
            {"customers": 0, "revenue": 0.0, "product_counts": defaultdict(int)},
        )
        count_i = int(customers or 0)
        bucket["customers"] += count_i
        bucket["revenue"] += float(revenue or 0)
        normalized = _normalize_active_product(str(product or ""))
        if normalized and normalized != "Unknown":
            bucket["product_counts"][normalized] += count_i

    return _format_ceragem_distribution_rows(stats_by_segment)


def _top_product_by_state(db: Session, upload_id: uuid.UUID | None) -> dict[str, str]:
    if upload_id:
        rows = (
            db.query(UploadRollup.scope, UploadRollup.key, UploadRollup.customer_count)
            .filter(
                UploadRollup.upload_id == upload_id,
                UploadRollup.dimension == "product",
                UploadRollup.key.isnot(None),
                UploadRollup.key != "Unknown",
            )
            .all()
        )
    else:
        rows = (
            db.query(
                UploadRollup.scope,
                UploadRollup.key,
                func.sum(UploadRollup.customer_count),
            )
            .filter(
                UploadRollup.dimension == "product",
                UploadRollup.key.isnot(None),
                UploadRollup.key != "Unknown",
            )
            .group_by(UploadRollup.scope, UploadRollup.key)
            .all()
        )

    if rows:
        segments_by_state = _modal_segment_by_state(db, upload_id)
        best: dict[str, tuple[int, str]] = {}
        for state, product, count in rows:
            key = state or "Unknown"
            normalized = _normalize_active_product(str(product))
            cnt = int(count or 0)
            current = best.get(key)
            if current is None or cnt > current[0]:
                best[key] = (
                    cnt,
                    standing_promo_outreach_product(
                        normalized,
                        ceragem_segment=segments_by_state.get(key),
                    ),
                )
        return {state: product for state, (_, product) in best.items()}

    counts = (
        db.query(
            Customer.state.label("state"),
            CustomerIntelligence.recommended_product.label("product"),
            func.count(CustomerIntelligence.id).label("cnt"),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(CustomerIntelligence.recommended_product.isnot(None))
    )
    if upload_id:
        counts = counts.filter(Customer.upload_id == upload_id)
    counts = counts.group_by(Customer.state, CustomerIntelligence.recommended_product).subquery()

    ranked = (
        db.query(
            counts.c.state,
            counts.c.product,
            func.row_number()
            .over(partition_by=counts.c.state, order_by=counts.c.cnt.desc())
            .label("rn"),
        )
    ).subquery()

    live_rows = db.query(ranked.c.state, ranked.c.product).filter(ranked.c.rn == 1).all()
    segments_by_state = _modal_segment_by_state(db, upload_id)
    return {
        (state or "Unknown"): standing_promo_outreach_product(
            _normalize_active_product(product),
            ceragem_segment=segments_by_state.get(state or "Unknown"),
        )
        for state, product in live_rows
    }


def _attach_state_intelligence(db: Session, rows: list[dict], upload_id: uuid.UUID | None) -> list[dict]:
    geo_bundle = _state_geo_bundle_by_state(db, upload_id)
    products = _top_product_by_state(db, upload_id)
    max_revenue = max((float(row.get("revenue") or 0) for row in rows), default=1.0)
    enriched: list[dict] = []
    for row in rows:
        state = row.get("state") or "Unknown"
        scores = geo_bundle.get(state, {})
        enriched.append(
            {
                **row,
                **scores,
                "top_product": products.get(state),
            }
        )
    for row in enriched:
        row["opportunity_score"] = compute_state_opportunity_score(row, max_revenue=max_revenue)
    return apply_radar_axis_spreads(enriched)


def _rank_top_zips(rows: list[dict], *, limit: int) -> list[dict]:
    if not rows:
        return []
    max_revenue = max(float(row.get("revenue") or 0) for row in rows)
    for row in rows:
        row["customers"] = int(row.get("customers") or 0)
        raw_product = row.get("recommended_product") or row.get("top_product") or row.get("intelligence_product")
        row["intelligence_product"] = raw_product
        promo = standing_promo_outreach_product(
            raw_product,
            purchase_power=row.get("purchase_power"),
            ceragem_segment=row.get("ceragem_segment"),
        )
        row["promo_outreach_product"] = promo
        row["top_product"] = promo
        row["opportunity_score"] = compute_zip_opportunity_score(row, max_revenue=max_revenue)
    ranked = sorted(rows, key=lambda row: -(row.get("opportunity_score") or 0))
    return _select_diverse_top_zips(
        ranked,
        limit=limit,
        max_per_state=RECENT_OPPORTUNITIES_MAX_PER_STATE,
    )


def _select_diverse_top_zips(rows: list[dict], *, limit: int, max_per_state: int) -> list[dict]:
    """Pick nationwide TOP ZIPs with per-state and V/M/S series diversity."""
    selected: list[dict] = []
    state_counts: dict[str, int] = {}
    selected_ids: set[int] = set()

    def can_add(row: dict) -> bool:
        state = str(row.get("state") or "Unknown")
        if state_counts.get(state, 0) >= max_per_state:
            return False
        return id(row) not in selected_ids

    def add(row: dict) -> None:
        state = str(row.get("state") or "Unknown")
        selected.append(row)
        selected_ids.add(id(row))
        state_counts[state] = state_counts.get(state, 0) + 1

    for series in RECENT_OPPORTUNITIES_TARGET_SERIES:
        if len(selected) >= limit:
            break
        for row in rows:
            product = row.get("intelligence_product") or row.get("recommended_product")
            if _product_series_code(product) != series:
                continue
            if not can_add(row):
                continue
            add(row)
            break

    for row in rows:
        if len(selected) >= limit:
            break
        if not can_add(row):
            continue
        add(row)

    return selected


def _modal_value_by_zip(
    db: Session,
    upload_id: uuid.UUID | None,
    column: str,
) -> dict[tuple[str, str], str]:
    model_col = getattr(CustomerIntelligence, column)
    q = (
        db.query(
            Customer.state.label("state"),
            Customer.zip.label("zip"),
            model_col.label("value"),
            func.count(Customer.customer_id).label("cnt"),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(
            Customer.zip.isnot(None),
            Customer.zip != "",
            Customer.zip != "Unknown",
            model_col.isnot(None),
        )
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    counts = q.group_by(Customer.state, Customer.zip, model_col).subquery()
    ranked = (
        db.query(
            counts.c.state,
            counts.c.zip,
            counts.c.value,
            func.row_number()
            .over(partition_by=[counts.c.state, counts.c.zip], order_by=counts.c.cnt.desc())
            .label("rn"),
        )
    ).subquery()
    rows = db.query(ranked.c.state, ranked.c.zip, ranked.c.value).filter(ranked.c.rn == 1).all()
    return {
        (state or "Unknown", zip_code or "Unknown"): str(value)
        for state, zip_code, value in rows
    }


def _nationwide_zip_intelligence_rows(db: Session, upload_id: uuid.UUID | None) -> list[dict]:
    """Aggregate live intelligence by ZIP across the US for Recent Opportunities."""
    products_by_zip = _modal_value_by_zip(db, upload_id, "recommended_product")
    segments_by_zip = _modal_value_by_zip(db, upload_id, "ceragem_segment")

    q = (
        db.query(
            Customer.state,
            Customer.zip,
            func.max(Customer.city).label("city"),
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_conversion),
            func.sum(CustomerIntelligence.expected_revenue),
            func.avg(CustomerIntelligence.purchase_power_index),
            func.avg(CustomerIntelligence.campaign_priority),
            func.avg(CustomerIntelligence.pain_index),
            func.avg(CustomerIntelligence.lifestyle_index),
            func.avg(CustomerIntelligence.brand_familiarity_index),
            func.avg(CustomerIntelligence.baseline_conversion),
            func.avg(CustomerIntelligence.promo_uplift),
            func.avg(CustomerIntelligence.expected_conversion),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(
            Customer.zip.isnot(None),
            Customer.zip != "",
            Customer.zip != "Unknown",
        )
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)

    # Rank in Python via compute_zip_opportunity_score — do not pre-filter by intelligence_rank
    # or affluent suburban ZIPs (High+ · Wellness / V9) monopolize the candidate pool.
    rows = (
        q.group_by(Customer.state, Customer.zip)
        .having(func.count(Customer.customer_id) >= RECENT_OPPORTUNITIES_MIN_ZIP_CUSTOMERS)
        .all()
    )

    out: list[dict] = []
    for (
        state,
        zip_code,
        city,
        count,
        orders,
        revenue,
        pp_avg,
        cp_avg,
        pain_avg,
        ls_avg,
        brand_avg,
        baseline_avg,
        promo_uplift_avg,
        uplifted_conv_avg,
    ) in rows:
        state_key = state or "Unknown"
        zip_key = zip_code or "Unknown"
        zip_pair = (state_key, zip_key)
        count_i = int(count or 0)
        orders_f = float(orders or 0)
        pp_level = _index_level_from_float(pp_avg)
        cp_level = _index_level_from_float(cp_avg)
        raw_product = products_by_zip.get(zip_pair)
        segment = segments_by_zip.get(zip_pair) or "Mid-Low + Pain Index"
        out.append(
            {
                "zip": zip_key,
                "state": state_key,
                "city": city,
                "revenue": round(float(revenue or 0), 2),
                "orders": round(orders_f, 2),
                "customers": count_i,
                "conversion": round(
                    float(uplifted_conv_avg or 0) or orders_f / max(count_i, 1),
                    4,
                ),
                "baseline_conversion": round(float(baseline_avg or 0), 6),
                "promo_uplift": round(float(promo_uplift_avg or 0), 6),
                "purchase_power": pp_level,
                "campaign_priority": cp_level,
                "purchase_power_index_score": _index_pct(pp_avg),
                "campaign_priority_index_score": _index_pct(cp_avg),
                "pain_index_score": _index_pct(pain_avg),
                "lifestyle_index_score": _index_pct(ls_avg),
                "brand_index_score": _index_pct(brand_avg),
                "ceragem_segment": segment,
                "recommended_product": raw_product,
                "top_product": standing_promo_outreach_product(
                    raw_product,
                    purchase_power=pp_level,
                    ceragem_segment=segment,
                ),
            }
        )
    return out


def _rollup_zip_candidates(
    db: Session,
    upload_id: uuid.UUID | None,
    segments_by_state: dict[str, str],
    products_by_state: dict[str, str],
    *,
    candidate_limit: int,
) -> list[dict]:
    """Fast path — pre-aggregated UploadRollup zip rows (avoids nationwide live scan)."""
    out: list[dict] = []
    if upload_id:
        rollups = (
            db.query(UploadRollup)
            .filter(UploadRollup.upload_id == upload_id, UploadRollup.dimension == "zip")
            .order_by(UploadRollup.expected_revenue.desc())
            .limit(candidate_limit)
            .all()
        )
        for r in rollups:
            payload = _parse_rollup_payload(r.payload_json)
            customers = int(r.customer_count or 0)
            if customers <= 0:
                continue
            orders = float(r.expected_orders or 0)
            state = r.scope or "Unknown"
            recommended = payload.get("recommended_product") or products_by_state.get(state)
            segment = payload.get("ceragem_segment") or segments_by_state.get(state)
            out.append(
                {
                    "zip": r.key,
                    "state": state,
                    "city": payload.get("city"),
                    "revenue": round(float(r.expected_revenue or 0), 2),
                    "orders": round(orders, 2),
                    "customers": customers,
                    "conversion": round(orders / max(customers, 1), 4),
                    "purchase_power": payload.get("purchase_power"),
                    "campaign_priority": payload.get("campaign_priority"),
                    "recommended_product": recommended,
                    "ceragem_segment": segment,
                    "intelligence_product": recommended,
                    "top_product": standing_promo_outreach_product(
                        recommended,
                        purchase_power=payload.get("purchase_power"),
                        ceragem_segment=segment,
                    ),
                }
            )
        return out

    rollups = (
        db.query(
            UploadRollup.key,
            UploadRollup.scope,
            func.sum(UploadRollup.customer_count),
            func.sum(UploadRollup.expected_orders),
            func.sum(UploadRollup.expected_revenue),
            func.max(UploadRollup.payload_json),
        )
        .filter(UploadRollup.dimension == "zip")
        .group_by(UploadRollup.key, UploadRollup.scope)
        .order_by(func.sum(UploadRollup.expected_revenue).desc())
        .limit(candidate_limit)
        .all()
    )
    for zip_code, state, count, orders, revenue, payload_json in rollups:
        customers = int(count or 0)
        if customers <= 0:
            continue
        payload = _parse_rollup_payload(payload_json)
        state_key = state or "Unknown"
        recommended = payload.get("recommended_product") or products_by_state.get(state_key)
        segment = payload.get("ceragem_segment") or segments_by_state.get(state_key)
        orders_f = float(orders or 0)
        out.append(
            {
                "zip": zip_code or "Unknown",
                "state": state_key,
                "city": payload.get("city"),
                "revenue": round(float(revenue or 0), 2),
                "orders": round(orders_f, 2),
                "customers": customers,
                "conversion": round(orders_f / max(customers, 1), 4),
                "purchase_power": payload.get("purchase_power"),
                "campaign_priority": payload.get("campaign_priority"),
                "recommended_product": recommended,
                "ceragem_segment": segment,
                "intelligence_product": recommended,
                "top_product": standing_promo_outreach_product(
                    recommended,
                    purchase_power=payload.get("purchase_power"),
                    ceragem_segment=segment,
                ),
            }
        )
    return out


def _top_zips(db: Session, upload_id: uuid.UUID | None, limit: int = RECENT_OPPORTUNITIES_ZIP_LIMIT) -> list[dict]:
    """Nationwide TOP ZIPs ranked by composite intelligence (PP, priority, conversion, revenue)."""
    segments_by_state = _modal_segment_by_state(db, upload_id)
    products_by_state = _top_product_by_state(db, upload_id)
    candidate_limit = max(limit * 250, 500)

    rollup_candidates = _rollup_zip_candidates(
        db,
        upload_id,
        segments_by_state,
        products_by_state,
        candidate_limit=candidate_limit,
    )
    if rollup_candidates:
        return _rank_top_zips(rollup_candidates, limit=limit)

    candidates = _nationwide_zip_intelligence_rows(db, upload_id)
    if candidates:
        return _rank_top_zips(candidates, limit=limit)

    rows = (
        db.query(
            Customer.zip,
            Customer.state,
            func.max(Customer.city).label("city"),
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_conversion),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if upload_id:
        rows = rows.filter(Customer.upload_id == upload_id)
    rows = (
        rows.group_by(Customer.state, Customer.zip)
        .order_by(func.sum(CustomerIntelligence.expected_revenue).desc())
        .limit(candidate_limit)
        .all()
    )

    out = []
    for zip_code, state, city, count, orders, revenue in rows:
        count_i = int(count or 0)
        orders_f = float(orders or 0)
        out.append(
            {
                "zip": zip_code or "Unknown",
                "state": state or "Unknown",
                "city": city,
                "revenue": round(float(revenue or 0), 2),
                "orders": round(orders_f, 2),
                "customers": count_i,
                "conversion": round(orders_f / max(count_i, 1), 4),
            }
        )
    return _rank_top_zips(out, limit=limit)


def _segment_performance(db: Session, upload_id: uuid.UUID | None, limit: int = 8) -> list[dict]:
    if upload_id:
        rollups = (
            db.query(
                UploadRollup.key,
                func.sum(UploadRollup.customer_count),
                func.sum(UploadRollup.expected_orders),
                func.sum(UploadRollup.expected_revenue),
            )
            .filter(UploadRollup.upload_id == upload_id, UploadRollup.dimension == "ceragem")
            .group_by(UploadRollup.key)
            .all()
        )
    else:
        rollups = (
            db.query(
                UploadRollup.key,
                func.sum(UploadRollup.customer_count),
                func.sum(UploadRollup.expected_orders),
                func.sum(UploadRollup.expected_revenue),
            )
            .filter(UploadRollup.dimension == "ceragem")
            .group_by(UploadRollup.key)
            .all()
        )
    if rollups:
        out = []
        for segment, count, orders, revenue in rollups:
            count_i = int(count or 0)
            orders_f = float(orders or 0)
            out.append(
                {
                    "segment": segment or "Unknown",
                    "customers": count_i,
                    "revenue": round(float(revenue or 0), 2),
                    "orders": round(orders_f, 2),
                    "conversion": round(orders_f / max(count_i, 1), 4),
                }
            )
        return sorted(out, key=lambda x: -x["revenue"])[:limit]

    rows = (
        db.query(
            CustomerIntelligence.ceragem_segment,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_conversion),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
    )
    if upload_id:
        rows = rows.filter(Customer.upload_id == upload_id)
    rows = rows.group_by(CustomerIntelligence.ceragem_segment).all()

    out = []
    for segment, count, orders, revenue in rows:
        count_i = int(count or 0)
        orders_f = float(orders or 0)
        out.append(
            {
                "segment": segment or "Unknown",
                "customers": count_i,
                "revenue": round(float(revenue or 0), 2),
                "orders": round(orders_f, 2),
                "conversion": round(orders_f / max(count_i, 1), 4),
            }
        )
    return sorted(out, key=lambda x: -x["revenue"])[:limit]


def _product_distribution_from_rollups(rollups: list) -> list[dict]:
        merged: dict[str, list[float | int]] = defaultdict(lambda: [0.0, 0])
        for product, revenue, count in rollups:
            key = _normalize_active_product(product)
            merged[key][0] += float(revenue or 0)
            merged[key][1] += int(count or 0)
        ranked = sorted(merged.items(), key=lambda r: -r[1][0])
        total_revenue = sum(vals[0] for _, vals in ranked)
        out = []
        for product, (revenue, count) in ranked:
            rev = float(revenue or 0)
            out.append(
                {
                    "product": product,
                    "revenue": round(rev, 2),
                    "customers": int(count or 0),
                    "share_pct": round((rev / total_revenue * 100) if total_revenue else 0, 1),
                }
            )
        return out


def _product_distribution_from_intelligence(db: Session, upload_id: uuid.UUID | None) -> list[dict]:
    if upload_id:
        rows = (
            db.query(
                CustomerIntelligence.recommended_product,
                func.sum(CustomerIntelligence.expected_revenue),
                func.count(CustomerIntelligence.id),
            )
            .join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
            .filter(Customer.upload_id == upload_id)
            .group_by(CustomerIntelligence.recommended_product)
            .all()
        )
    else:
        rows = (
            db.query(
                CustomerIntelligence.recommended_product,
                func.sum(CustomerIntelligence.expected_revenue),
                func.count(CustomerIntelligence.id),
            )
            .group_by(CustomerIntelligence.recommended_product)
            .all()
        )

    merged_rows: dict[str, list[float | int]] = defaultdict(lambda: [0.0, 0])
    for product, revenue, count in rows:
        key = _normalize_active_product(product)
        merged_rows[key][0] += float(revenue or 0)
        merged_rows[key][1] += int(count or 0)

    ranked = sorted(merged_rows.items(), key=lambda r: -r[1][0])
    total_revenue = sum(vals[0] for _, vals in ranked)
    out = []
    for product, (revenue, count) in ranked:
        rev = float(revenue or 0)
        out.append(
            {
                "product": product,
                "revenue": round(rev, 2),
                "customers": int(count or 0),
                "share_pct": round((rev / total_revenue * 100) if total_revenue else 0, 1),
            }
        )
    return out


def _product_distribution(db: Session, upload_id: uuid.UUID | None) -> list[dict]:
    if upload_id:
        rollups = (
            db.query(
                UploadRollup.key,
                func.sum(UploadRollup.expected_revenue),
                func.sum(UploadRollup.customer_count),
            )
            .filter(UploadRollup.upload_id == upload_id, UploadRollup.dimension == "product")
            .group_by(UploadRollup.key)
            .all()
        )
        if rollups:
            return _product_distribution_from_rollups(rollups)

    # Global scope: never sum rollups across uploads (duplicates customers per file).
    if upload_id is None:
        mv_rows = read_mv_product_performance(db)
        if mv_rows:
            return mv_rows

    return _product_distribution_from_intelligence(db, upload_id)


def _revenue_over_time(db: Session, upload_id: uuid.UUID | None) -> list[dict]:
    q = (
        db.query(UploadHistory, RawUpload)
        .join(RawUpload, RawUpload.upload_id == UploadHistory.upload_id)
        .order_by(UploadHistory.created_at.asc())
    )
    if upload_id:
        q = q.filter(UploadHistory.upload_id == upload_id)

    cumulative_revenue = 0.0
    cumulative_orders = 0.0
    points: list[dict] = []

    for history, upload in q.all():
        upload_totals = (
            db.query(
                func.sum(UploadRollup.expected_revenue),
                func.sum(UploadRollup.expected_orders),
            )
            .filter(
                UploadRollup.upload_id == history.upload_id,
                UploadRollup.dimension == "state",
                UploadRollup.scope == "*",
            )
            .one()
        )
        rev = float(upload_totals[0] or 0)
        orders = float(upload_totals[1] or 0)
        if rev == 0 and orders == 0:
            fallback = (
                db.query(
                    func.sum(CustomerIntelligence.expected_revenue),
                    func.sum(CustomerIntelligence.expected_conversion),
                )
                .join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
                .filter(Customer.upload_id == history.upload_id)
                .one()
            )
            rev = float(fallback[0] or 0)
            orders = float(fallback[1] or 0)
        cumulative_revenue += rev
        cumulative_orders += orders
        label = format_app_date(history.created_at) if history.created_at else upload.filename
        customers = int(history.customer_count or 0)
        points.append(
            {
                "day": label,
                "revenue": round(cumulative_revenue, 2),
                "orders": round(cumulative_orders, 2),
                "customers": customers,
                "conversion_rate": round(orders / max(customers, 1), 6),
                "upload_id": str(history.upload_id),
                "file_name": upload.filename,
            }
        )

    if len(points) == 1:
        single = points[0]
        end_date = (
            db.query(UploadHistory.created_at).filter(UploadHistory.upload_id == uuid.UUID(single["upload_id"])).scalar()
        ) or datetime.utcnow()
        spread: list[dict] = []
        total_rev = single["revenue"]
        total_orders = single["orders"]
        for offset in range(6, -1, -1):
            day = end_date - timedelta(days=offset)
            factor = (6 - offset + 1) / 7
            spread.append(
                {
                    "day": format_app_date(day),
                    "revenue": round(total_rev * factor, 2),
                    "orders": round(total_orders * factor, 2),
                    "customers": single["customers"] if offset == 0 else 0,
                    "upload_id": single["upload_id"],
                    "file_name": single["file_name"],
                }
            )
        return spread
    return points


def _top_campaigns(db: Session, limit: int = 5) -> list[dict]:
    rows = (
        db.query(
            Campaign.campaign_name,
            func.sum(CampaignState.revenue),
            func.avg(CampaignState.roi),
            func.sum(CampaignState.sent),
        )
        .join(CampaignState, CampaignState.campaign_id == Campaign.campaign_id)
        .group_by(Campaign.campaign_id, Campaign.campaign_name)
        .order_by(func.sum(CampaignState.revenue).desc())
        .limit(limit)
        .all()
    )
    if not rows:
        return []

    return [
        {
            "name": name,
            "revenue": round(float(revenue or 0), 2),
            "roi": round(float(roi or 0), 4) if roi is not None else None,
            "sent": int(sent or 0),
        }
        for name, revenue, roi, sent in rows
    ]


def _index_level_expr(column):
    return case(
        (column >= 0.75, literal("High")),
        (column >= 0.45, literal("Medium")),
        else_=literal("Low"),
    )


PRIZM_LEVEL_HIGH = frozenset(
    {"Established Elite", "Suburban Sophisticates", "Booming with Confidence"},
)
PRIZM_LEVEL_MEDIUM = frozenset(
    {"Kids and Cul-de-Sacs", "Wellness Seekers", "Aging in Place", "Caregiving Households"},
)


def _prizm_level(segment: str | None) -> str:
    name = segment or "Unknown"
    if name in PRIZM_LEVEL_HIGH:
        return "High"
    if name in PRIZM_LEVEL_MEDIUM:
        return "Medium"
    return "Low"


def _ceragem_level(segment: str | None) -> str:
    from app.intelligence.ceragem_rules import parse_ceragem_tier

    tier = parse_ceragem_tier(segment)
    if tier == "High+":
        return "High"
    if tier in {"Mid-High+", "Mid+", "Mid-Low+"}:
        return "Medium"
    return "Low"


def _counts_to_band_pcts(counts: dict[str, int]) -> dict[str, int]:
    total = sum(counts.values()) or 1
    return {
        "high": round(counts.get("High", 0) / total * 100),
        "medium": round(counts.get("Medium", 0) / total * 100),
        "low": round(counts.get("Low", 0) / total * 100),
    }


def _grouped_index_distribution(db: Session, upload_id: uuid.UUID | None, column) -> dict[str, int]:
    level = _index_level_expr(column)
    q = (
        db.query(level, func.count(Customer.customer_id))
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    counts = {str(k or "Low"): int(v) for k, v in q.group_by(level).all()}
    return _counts_to_band_pcts(counts)


def _grouped_segment_distribution(
    db: Session,
    upload_id: uuid.UUID | None,
    column,
    level_fn,
) -> dict[str, int]:
    q = (
        db.query(column, func.count(Customer.customer_id))
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    counts = {"High": 0, "Medium": 0, "Low": 0}
    for segment, count in q.group_by(column).all():
        counts[level_fn(segment)] += int(count or 0)
    return _counts_to_band_pcts(counts)


def _index_band_count_exprs(column):
    return (
        func.sum(case((column >= 0.75, 1), else_=0)),
        func.sum(case((and_(column >= 0.45, column < 0.75), 1), else_=0)),
        func.sum(case((column < 0.45, 1), else_=0)),
    )


def _global_intelligence_aggregates(db: Session, upload_id: uuid.UUID | None):
    """Single customer-intelligence scan for radar + score-distribution widgets."""

    pp_high, pp_med, pp_low = _index_band_count_exprs(CustomerIntelligence.purchase_power_index)
    pain_high, pain_med, pain_low = _index_band_count_exprs(CustomerIntelligence.pain_index)
    life_high, life_med, life_low = _index_band_count_exprs(CustomerIntelligence.lifestyle_index)

    prizm_high = func.sum(
        case((CustomerIntelligence.prizm_proxy_segment.in_(tuple(PRIZM_LEVEL_HIGH)), 1), else_=0)
    )
    prizm_med = func.sum(
        case((CustomerIntelligence.prizm_proxy_segment.in_(tuple(PRIZM_LEVEL_MEDIUM)), 1), else_=0)
    )
    prizm_low = func.sum(
        case(
            (CustomerIntelligence.prizm_proxy_segment.in_(tuple(PRIZM_LEVEL_HIGH | PRIZM_LEVEL_MEDIUM)), 0),
            else_=1,
        )
    )

    cer_high = func.sum(case((CustomerIntelligence.ceragem_segment.like("High+%"), 1), else_=0))
    cer_med = func.sum(
        case(
            (CustomerIntelligence.ceragem_segment.like("Mid-High+%"), 1),
            (CustomerIntelligence.ceragem_segment.like("Mid+ ·%"), 1),
            (CustomerIntelligence.ceragem_segment.like("Mid-Low+%"), 1),
            # Legacy V04
            (CustomerIntelligence.ceragem_segment.like("Mid-High +%"), 1),
            (CustomerIntelligence.ceragem_segment.like("Mid-Low +%"), 1),
            else_=0,
        )
    )
    cer_low = func.sum(
        case(
            (CustomerIntelligence.ceragem_segment.like("High+%"), 0),
            (CustomerIntelligence.ceragem_segment.like("Mid-High+%"), 0),
            (CustomerIntelligence.ceragem_segment.like("Mid+ ·%"), 0),
            (CustomerIntelligence.ceragem_segment.like("Mid-Low+%"), 0),
            (CustomerIntelligence.ceragem_segment.like("Mid-High +%"), 0),
            (CustomerIntelligence.ceragem_segment.like("Mid-Low +%"), 0),
            else_=1,
        )
    )

    prizm_score = func.avg(
        case(
            (
                and_(
                    CustomerIntelligence.prizm_proxy_segment.isnot(None),
                    CustomerIntelligence.prizm_proxy_segment != "Unknown",
                ),
                0.85,
            ),
            else_=0.2,
        )
    )
    ceragem_score = func.avg(
        case(
            (CustomerIntelligence.ceragem_segment.like("High+%"), 0.9),
            (CustomerIntelligence.ceragem_segment.like("Mid-High+%"), 0.7),
            (CustomerIntelligence.ceragem_segment.like("Mid+ ·%"), 0.58),
            (CustomerIntelligence.ceragem_segment.like("Mid-Low+%"), 0.45),
            (CustomerIntelligence.ceragem_segment.like("Low+%"), 0.25),
            (CustomerIntelligence.ceragem_segment.like("High +%"), 0.9),
            (CustomerIntelligence.ceragem_segment.like("Mid-High +%"), 0.7),
            (CustomerIntelligence.ceragem_segment.like("Mid-Low +%"), 0.45),
            else_=0.25,
        )
    )
    recommendation_score = func.avg(CustomerIntelligence.campaign_priority)

    q = (
        db.query(
            pp_high,
            pp_med,
            pp_low,
            pain_high,
            pain_med,
            pain_low,
            life_high,
            life_med,
            life_low,
            prizm_high,
            prizm_med,
            prizm_low,
            cer_high,
            cer_med,
            cer_low,
            prizm_score,
            ceragem_score,
            recommendation_score,
        )
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
    )
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    return q.one()


def _intelligence_score_distribution(db: Session, upload_id: uuid.UUID | None, agg_row=None) -> list[dict]:
    """High / Medium / Low band percentages for Mission Control Intelligence Score Distribution."""

    row = agg_row if agg_row is not None else _global_intelligence_aggregates(db, upload_id)

    def row_from_counts(label: str, high: int, medium: int, low: int) -> dict:
        return {"label": label, **_counts_to_band_pcts({"High": int(high or 0), "Medium": int(medium or 0), "Low": int(low or 0)})}

    return [
        row_from_counts("Purchase Power", row[0], row[1], row[2]),
        row_from_counts("Pain Index", row[3], row[4], row[5]),
        row_from_counts("LifeStyle", row[6], row[7], row[8]),
        row_from_counts("PRIZM Proxy", row[9], row[10], row[11]),
        row_from_counts("Ceragem Segment", row[12], row[13], row[14]),
    ]


def _intelligence_radar(db: Session, upload_id: uuid.UUID | None, averages: dict, agg_row=None) -> list[dict]:
    """ORION DNA radar — customer intelligence dimensions from live DB aggregates."""

    def pct(value: float | None) -> float:
        if value is None:
            return 0.0
        return round(min(100.0, max(0.0, float(value) * 100)), 1)

    prizm_avg, ceragem_avg, recommendation_avg = (
        (agg_row[15], agg_row[16], agg_row[17])
        if agg_row is not None
        else _global_intelligence_aggregates(db, upload_id)[15:18]
    )

    return [
        {"axis": "Purchase Power", "score": pct(averages.get("purchase_power_index"))},
        {"axis": "Pain Index", "score": pct(averages.get("pain_index"))},
        {"axis": "Lifestyle", "score": pct(averages.get("lifestyle_index"))},
        {"axis": "PRIZM Proxy", "score": pct(prizm_avg)},
        {"axis": "Ceragem Segment", "score": pct(ceragem_avg)},
        {"axis": "Recommendation", "score": pct(recommendation_avg)},
    ]


def _recent_activity(db: Session, upload_id: uuid.UUID | None, limit: int = 5) -> list[dict]:
    activity: list[dict] = []

    upload_q = db.query(RawUpload).order_by(RawUpload.uploaded_date.desc())
    if upload_id:
        upload_q = upload_q.filter(RawUpload.upload_id == upload_id)
    for upload in upload_q.limit(3).all():
        summary = {}
        if upload.summary_json:
            try:
                summary = json.loads(upload.summary_json)
            except json.JSONDecodeError:
                summary = {}
        rows = int(summary.get("rows_processed") or summary.get("total_rows") or 0)
        activity.append(
            {
                "title": "New Customers Uploaded",
                "detail": f"{upload.filename} · {rows:,} records",
                "time": format_app_datetime(upload.uploaded_date) if upload.uploaded_date else "",
                "sort_key": upload.uploaded_date or datetime.min,
            }
        )

    audits = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    action_titles = {
        "upload_customer_file": "New Customers Uploaded",
        "create_campaign": "Campaign Created",
        "upload_campaign_report": "Campaign Report Received",
    }
    for row in audits:
        title = action_titles.get(row.action, row.action.replace("_", " ").title())
        detail = row.entity_id or row.status or ""
        activity.append(
            {
                "title": title,
                "detail": detail,
                "time": format_app_datetime(row.timestamp) if row.timestamp else "",
                "sort_key": row.timestamp or datetime.min,
            }
        )

    activity.sort(key=lambda x: x["sort_key"], reverse=True)
    deduped: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for item in activity:
        key = (item["title"], item["detail"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append({"title": item["title"], "detail": item["detail"], "time": item["time"]})
        if len(deduped) >= limit:
            break
    return deduped


def _approx_table_count(db: Session, table_name: str, exact_fallback) -> int:
    """Fast row-count estimate. On PostgreSQL uses planner statistics
    (pg_class.reltuples) to avoid multi-second sequential scans over very
    large, wide tables (customer_intelligence is 5GB+ heap). Falls back to an
    exact COUNT on other backends (e.g. SQLite used in tests)."""
    bind = db.get_bind()
    if bind is not None and bind.dialect.name.startswith("postgres"):
        estimate = db.execute(
            text("SELECT reltuples::bigint FROM pg_class WHERE relname = :t"),
            {"t": table_name},
        ).scalar()
        if estimate is not None and estimate > 0:
            return int(estimate)
    return int(exact_fallback() or 0)


def _system_status(db: Session) -> list[dict]:
    customer_count = _approx_table_count(
        db, "customers", lambda: db.query(func.count(Customer.customer_id)).scalar()
    )
    intel_count = _approx_table_count(
        db, "customer_intelligence", lambda: db.query(func.count(CustomerIntelligence.id)).scalar()
    )
    # Statistics-based estimates carry small drift, so treat near-complete
    # intelligence coverage (>=98%) as an operational pipeline.
    pipeline_ok = customer_count == 0 or intel_count >= customer_count * 0.98
    return [
        {"name": "Data Pipeline", "status": "Operational" if pipeline_ok else "Degraded"},
        {"name": "Intelligence Engine", "status": "Operational" if intel_count else "Idle"},
        {"name": "Recommendation Engine", "status": "Operational" if intel_count else "Idle"},
        {"name": "Commercial Intelligence", "status": f"v{get_runtime_version()}" if intel_count else "Idle"},
    ]


def _build_executive_dashboard(db: Session, upload_id: str | None = None) -> dict:
    uid = _parse_upload_id(upload_id)
    kpis = _aggregate_kpis(db, uid)
    state_rows = _attach_state_intelligence(db, _revenue_by_state(db, uid), uid)
    segment_rows = _segment_performance(db, uid)
    product_rows = _product_distribution(db, uid)
    global_aggs = _global_intelligence_aggregates(db, uid)

    prizm_q = (
        db.query(
            UploadRollup.key,
            func.sum(UploadRollup.expected_revenue),
        )
        .filter(UploadRollup.dimension == "prizm")
    )
    if uid:
        prizm_q = prizm_q.filter(UploadRollup.upload_id == uid)
    prizm_rows = prizm_q.group_by(UploadRollup.key).all()
    if not prizm_rows:
        fallback_q = (
            db.query(
                CustomerIntelligence.prizm_proxy_segment,
                func.sum(CustomerIntelligence.expected_revenue),
            )
            .join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
        )
        if uid:
            fallback_q = fallback_q.filter(Customer.upload_id == uid)
        prizm_rows = fallback_q.group_by(CustomerIntelligence.prizm_proxy_segment).all()

    top_opportunity = (
        max(state_rows, key=lambda row: float(row.get("opportunity_score") or 0))
        if state_rows
        else None
    )
    score_distribution = _intelligence_score_distribution(db, uid, global_aggs)
    pp_bands = _pp_bands_from_distribution(score_distribution)
    standing_opportunity_rows = build_standing_promo_opportunity_rows(db, uid, product_rows)
    highest_conversion = pick_highest_conversion_opportunity(
        db,
        uid,
        product_rows,
        segment_rows,
        pp_bands,
        targetable_customers=float(kpis.get("targetable_customers") or kpis.get("total_customers") or 0),
    )
    top_product_opportunity = (
        highest_conversion["product"]
        if highest_conversion
        else (standing_opportunity_rows[0]["product"] if standing_opportunity_rows else (product_rows[0]["product"] if product_rows else None))
    )

    return {
        **kpis,
        "campaign_roi": None,
        "top_performing_state": state_rows[0]["state"] if state_rows else None,
        "top_opportunity_state": top_opportunity["state"] if top_opportunity else None,
        "top_performing_segment": segment_rows[0]["segment"] if segment_rows else None,
        "top_product_opportunity": top_product_opportunity,
        "revenue_by_state": [{"state": r["state"], "revenue": r["revenue"]} for r in state_rows],
        "revenue_by_segment": [{"segment": r["segment"], "revenue": r["revenue"]} for r in segment_rows],
        "product_ranking": [{"product": r["product"], "revenue": r["revenue"]} for r in product_rows],
        "state_performance": state_rows,
        "radar_opportunities": _build_radar_opportunities(db, state_rows, uid),
        "top_zips": _top_zips(db, uid),
        "segment_performance": segment_rows,
        "product_distribution": product_rows,
        "revenue_over_time": _revenue_over_time(db, uid),
        "top_campaigns": _top_campaigns(db),
        "intelligence_radar": _intelligence_radar(db, uid, kpis["average_indices"], global_aggs),
        "intelligence_score_distribution": score_distribution,
        "purchase_power_distribution": _purchase_power_distribution(db, uid),
        "ceragem_distribution": _ceragem_distribution(db, uid),
        "recent_activity": _recent_activity(db, uid),
        "system_status": _system_status(db),
        "data_source": "live",
        "commercial_version": get_runtime_version(),
        "pricing_version": get_runtime_version(),
        "commercial_intelligence": build_commercial_intelligence_summary(
            db,
            uid,
            product_rows,
            float(kpis.get("expected_revenue") or 0),
            float(kpis.get("expected_orders") or 0),
            float(kpis.get("le_frame_incentive") or 0),
            float(kpis.get("targetable_customers") or kpis.get("total_customers") or 0),
            segment_rows=segment_rows,
            pp_bands=pp_bands,
        ),
        "scoped_upload_id": str(uid) if uid else None,
        "prizm_revenue": [{"segment": s or "Unknown", "revenue": round(float(r or 0), 2)} for s, r in prizm_rows],
    }


def build_executive_dashboard(db: Session, upload_id: str | None = None) -> dict:
    upload_scope = str(upload_id) if upload_id else "all"
    scope = f"{EXECUTIVE_DASHBOARD_BUILD_VERSION}:{upload_scope}"
    return cached_dashboard("executive", scope, lambda: _build_executive_dashboard(db, upload_id))


def get_executive_summary(db: Session, upload_id: str | None = None) -> dict:
    """Backward-compatible entry — returns live executive dashboard payload."""
    return build_executive_dashboard(db, upload_id)
