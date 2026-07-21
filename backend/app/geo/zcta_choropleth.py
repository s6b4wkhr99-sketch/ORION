"""ZCTA choropleth GeoJSON for state-level ZIP heatmaps."""

from __future__ import annotations

import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.cache.dashboard_cache import DASHBOARD_BUILD_VERSION, cached_dashboard
from app.campaign.dashboards import _get_state_dashboard, _parse_upload_id
from app.geo.zcta_geo_loader import NATIONAL_GEOJSON, load_state_zcta_geojson
from app.mapping.standardization import standardize_zip
from app.market.cbsa_geo import geometry_centroid, nearest_cbsa
from app.market.cbsa_reference import cbsa_meta
from app.models.customer import Customer, CustomerIntelligence
from app.models.reference_data import ZipMaster
from app.models.zip import ZipIntelligence

GEO_DIR = Path(__file__).resolve().parents[2] / "data" / "geo"

# Coordinate precision for choropleth geometry. 3 decimals ≈ 110m — far below one pixel at
# state-level zoom, but cuts payload size (and client parse/render cost) substantially.
_COORD_PRECISION = 3


def _round_ring(ring: list) -> list | None:
    out: list = []
    last: tuple[float, float] | None = None
    for pt in ring:
        if not isinstance(pt, (list, tuple)) or len(pt) < 2:
            continue
        lon = round(float(pt[0]), _COORD_PRECISION)
        lat = round(float(pt[1]), _COORD_PRECISION)
        if last is not None and lon == last[0] and lat == last[1]:
            continue  # drop consecutive duplicate points created by rounding
        out.append([lon, lat])
        last = (lon, lat)
    if len(out) < 4:
        return None
    if out[0] != out[-1]:
        out.append(out[0])
    return out


def _round_geometry(geom: dict | None) -> dict | None:
    if not geom:
        return geom
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if gtype == "Polygon" and coords:
        rings = [r for r in (_round_ring(ring) for ring in coords) if r]
        return {"type": "Polygon", "coordinates": rings} if rings else geom
    if gtype == "MultiPolygon" and coords:
        polys = []
        for poly in coords:
            rings = [r for r in (_round_ring(ring) for ring in poly) if r]
            if rings:
                polys.append(rings)
        return {"type": "MultiPolygon", "coordinates": polys} if polys else geom
    return geom


@lru_cache(maxsize=1)
def _load_national_zcta() -> dict | None:
    if not NATIONAL_GEOJSON.exists():
        return None
    try:
        return json.loads(NATIONAL_GEOJSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _strip_cache_meta(payload: dict) -> dict:
    return {k: v for k, v in payload.items() if k != "cache_hit"}


def _zip_product_scores(db: Session, upload_id: str | None, state: str) -> dict[str, dict[str, dict]]:
    scope = f"{DASHBOARD_BUILD_VERSION}:{upload_id or 'all'}:{state}:ladder-v6-m10-v7-geo"
    return _strip_cache_meta(
        cached_dashboard(
            "zip_product_scores",
            scope,
            lambda: _compute_zip_product_scores(db, upload_id, state),
        )
    )


def _compute_zip_product_scores(db: Session, upload_id: str | None, state: str) -> dict[str, dict[str, dict]]:
    """Per-ZIP recommended-product mix for choropleth product-legend filtering."""
    from app.intelligence.ladder_opportunity import (
        aggregate_ladder_geo_product_opportunity,
        merge_zip_product_scores,
    )

    uid = _parse_upload_id(upload_id)
    q = (
        db.query(
            Customer.zip,
            CustomerIntelligence.recommended_product,
            func.count(Customer.customer_id),
            func.sum(CustomerIntelligence.expected_revenue),
        )
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(Customer.state == state, CustomerIntelligence.recommended_product.isnot(None))
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)

    primary: dict[str, dict[str, dict]] = defaultdict(dict)
    for zip_code, product, count, revenue in q.group_by(Customer.zip, CustomerIntelligence.recommended_product).all():
        if not zip_code or not product:
            continue
        normalized = standardize_zip(str(zip_code).strip()) or str(zip_code).strip()
        primary[normalized][str(product)] = {
            "expected_revenue": round(float(revenue or 0), 2),
            "target_customers": int(count or 0),
        }

    ladder = aggregate_ladder_geo_product_opportunity(db, uid, state, "zip")
    merged = merge_zip_product_scores(dict(primary), ladder)
    return _apply_geo_gated_m10_outreach_credit(db, merged)


_M10_CHOROPLETH_DONOR_SKUS = ("Pause M6", "Pause M6s", "Pause M4", "Master V7")


def _zip_choropleth_m10_eligible(zi: ZipIntelligence | None) -> bool:
    """Affluent-ZIP gate for Pause M10 choropleth — matches is_m10_eligible_zip + post-promo price."""
    from app.geo.zip_economics import income_tier
    from app.intelligence.product_ladders import is_m10_eligible_zip
    from app.intelligence.promo_price_response import is_post_promo_accessible

    if zi is None:
        return False
    premium = bool(zi.top50_rank)
    tier = income_tier(zi.median_income, premium_zip=premium)
    if premium or tier == "High":
        pp_category = "High"
    elif tier == "Mid":
        pp_category = "Medium"
    else:
        pp_category = "Low"

    if not is_m10_eligible_zip(
        premium_zip=premium,
        zip_income_tier=tier,
        purchase_power_category=pp_category,
    ):
        return False
    return is_post_promo_accessible(
        "Pause M10",
        purchase_power_category=pp_category,
        zip_income_tier=tier,
    )


def _apply_geo_gated_m10_outreach_credit(
    db: Session,
    merged: dict[str, dict[str, dict]],
) -> dict[str, dict[str, dict]]:
    """Credit wellness/up-line donors to Pause M10 in M10-eligible ZIPs only (never V9 — flagship path)."""
    if not merged:
        return merged

    zip_codes = list(merged.keys())
    rows = db.query(ZipIntelligence).filter(ZipIntelligence.zip.in_(zip_codes)).all()
    zi_by_zip = {str(row.zip): row for row in rows if row.zip}

    for zip_code, products in merged.items():
        if not _zip_choropleth_m10_eligible(zi_by_zip.get(zip_code)):
            continue
        donor_revenue = 0.0
        donor_customers = 0
        for donor in _M10_CHOROPLETH_DONOR_SKUS:
            row = products.get(donor) or {}
            donor_revenue += float(row.get("expected_revenue") or 0)
            donor_customers += int(row.get("target_customers") or 0)
        if donor_revenue <= 0 and donor_customers <= 0:
            continue
        existing = products.get("Pause M10") or {"expected_revenue": 0.0, "target_customers": 0}
        products["Pause M10"] = {
            "expected_revenue": round(float(existing.get("expected_revenue") or 0) + donor_revenue, 2),
            "target_customers": int(existing.get("target_customers") or 0) + donor_customers,
        }

    return merged


def _zip_scores(db: Session, upload_id: str | None, state: str, zip_limit: int = 500) -> dict[str, dict]:
    # Cache per (upload, state): the state dashboard compute is the cold-path cost of a metro
    # heatmap build, and every metro that touches this state can reuse the same scores.
    scope = f"{DASHBOARD_BUILD_VERSION}:{upload_id or 'all'}:{state}:{zip_limit}"
    return _strip_cache_meta(
        cached_dashboard("zip_scores", scope, lambda: _compute_zip_scores(db, upload_id, state, zip_limit))
    )


def _attach_product_scores(scores: dict[str, dict], product_scores: dict[str, dict[str, dict]]) -> dict[str, dict]:
    for zip_code, row in scores.items():
        row["revenue_by_product"] = product_scores.get(zip_code, {})
    return scores


def _merge_feature_props(
    zip_code: str,
    score: dict | None,
    product_scores: dict[str, dict[str, dict]],
) -> dict:
    revenue_by_product = product_scores.get(zip_code, {})
    if score is not None:
        return {**score, "revenue_by_product": revenue_by_product}
    return {
        "zip": zip_code,
        "expected_revenue": 0.0,
        "target_customers": 0,
        "opportunity_score": 0,
        "revenue_by_product": revenue_by_product,
    }


def _compute_zip_scores(db: Session, upload_id: str | None, state: str, zip_limit: int = 500) -> dict[str, dict]:
    # The choropleth only needs zip / city / revenue / customers, so we use the base state
    # dashboard directly and skip enrich_state_dashboard (extra demographic + geo queries).
    payload = _get_state_dashboard(db, upload_id, state, zip_limit=zip_limit)
    scores: dict[str, dict] = {}
    for row in payload.get("zip_opportunity") or []:
        raw_zip = row.get("zip")
        if not raw_zip or raw_zip == "Unknown":
            continue
        # Customer/rollup ZIP keys are often unpadded (e.g. "1201"); ZCTA geo uses 5-digit codes ("01201").
        zip_code = standardize_zip(str(raw_zip).strip()) or str(raw_zip).strip()
        revenue = float(row.get("expected_revenue") or 0)
        customers = int(row.get("target_customers") or 0)
        scores[zip_code] = {
            "zip": zip_code,
            "city": row.get("city"),
            "expected_revenue": revenue,
            "target_customers": customers,
            "opportunity_score": min(99, round(revenue / 1000 + customers * 0.5)),
        }
    return scores


def _zip_to_county_map(db: Session, state: str, zips: list[str]) -> dict[str, str]:
    """Resolve ZIP → county name from reference tables and customer city data."""
    if not zips:
        return {}

    mapping: dict[str, str] = {}
    for ref in db.query(ZipIntelligence).filter(ZipIntelligence.zip.in_(zips)).all():
        if ref.county:
            mapping[ref.zip] = ref.county

    missing = [z for z in zips if z not in mapping]
    if missing:
        for ref in db.query(ZipMaster).filter(ZipMaster.zip_code.in_(missing)).all():
            if ref.county:
                mapping[ref.zip_code] = ref.county

    still_missing = [z for z in zips if z not in mapping]
    if still_missing:
        rows = (
            db.query(Customer.zip, Customer.city, func.count(Customer.customer_id))
            .filter(Customer.zip.in_(still_missing), Customer.state == state)
            .group_by(Customer.zip, Customer.city)
            .all()
        )
        city_by_zip: dict[str, tuple[str, int]] = {}
        for zip_code, city, count in rows:
            if not zip_code or not city:
                continue
            prev = city_by_zip.get(zip_code)
            if not prev or int(count or 0) > prev[1]:
                city_by_zip[zip_code] = (city, int(count or 0))
        for zip_code, (city, _) in city_by_zip.items():
            mapping.setdefault(zip_code, city)

    return mapping


def _county_fallback_features(db: Session, state: str, scores: dict[str, dict]) -> list[dict]:
    """Aggregate ZIP metrics to county when ZCTA polygons are not bundled."""
    zips = list(scores.keys())
    zip_county = _zip_to_county_map(db, state, zips)
    county_stats: dict[str, dict] = defaultdict(lambda: {"expected_revenue": 0.0, "target_customers": 0, "zips": 0})

    for zip_code, row in scores.items():
        county = zip_county.get(zip_code) or "Unknown"
        bucket = county_stats[county]
        bucket["expected_revenue"] += row["expected_revenue"]
        bucket["target_customers"] += row["target_customers"]
        bucket["zips"] += 1

    features = []
    for county, stats in county_stats.items():
        if county == "Unknown" and stats["zips"] == 0:
            continue
        features.append(
            {
                "type": "Feature",
                "id": county,
                "properties": {
                    "name": county,
                    "county": county,
                    "state": state,
                    **stats,
                    "opportunity_score": min(99, round(stats["expected_revenue"] / 1000)),
                },
                "geometry": None,
            }
        )
    return features


def get_state_zcta_choropleth(db: Session, upload_id: str | None, state: str) -> dict:
    state = (state or "").strip().upper()
    if not state:
        return {"type": "FeatureCollection", "features": [], "meta": {"error": "state required"}}
    # Building the full-state choropleth (scores + geometry merge + rounding) is expensive, so cache
    # the result. Cache generation is bumped on new uploads, keeping it consistent with other dashboards.
    scope = f"{DASHBOARD_BUILD_VERSION}:{upload_id or 'all'}:{state}"
    return cached_dashboard("zcta", scope, lambda: _build_state_zcta_choropleth(db, upload_id, state))


def _build_state_zcta_choropleth(db: Session, upload_id: str | None, state: str) -> dict:
    product_scores = _zip_product_scores(db, upload_id, state)
    scores = _attach_product_scores(_zip_scores(db, upload_id, state), product_scores)
    if not scores and not product_scores:
        return {"type": "FeatureCollection", "features": [], "meta": {"state": state, "count": 0}}

    # Prefer the state-specific source so we can safely render EVERY ZCTA in the state (including
    # zones without customer data) for geographic context. Only fall back to the national file when
    # no state source exists — and in that case keep the score filter so we don't draw the whole US.
    state_source = load_state_zcta_geojson(state)
    zcta_source = state_source or _load_national_zcta()
    source_is_state_specific = state_source is not None
    features: list[dict] = []
    scored_count = 0
    geometry_source = "zcta500k"

    if zcta_source and zcta_source.get("features"):
        for feature in zcta_source["features"]:
            props = feature.get("properties") or {}
            zip_code = str(props.get("ZCTA5CE20") or props.get("GEOID20") or props.get("ZCTA5") or props.get("zip") or "").zfill(5)
            if len(zip_code) != 5:
                continue
            st = str(props.get("STUSPS") or props.get("state") or "").upper()
            if st and st != state:
                continue
            score = scores.get(zip_code)
            # National fallback without state metadata: only keep scored ZIPs to avoid rendering
            # every ZCTA in the country when we can't confirm the zone belongs to this state.
            if score is None and not source_is_state_specific and not st:
                continue
            if score is not None or product_scores.get(zip_code):
                merged_props = _merge_feature_props(zip_code, score, product_scores)
                if score is not None or any(
                    p.get("expected_revenue", 0) > 0 for p in product_scores.get(zip_code, {}).values()
                ):
                    scored_count += 1
            else:
                merged_props = _merge_feature_props(zip_code, None, product_scores)
            features.append(
                {
                    "type": "Feature",
                    "id": zip_code,
                    "properties": merged_props,
                    "geometry": _round_geometry(feature.get("geometry")),
                }
            )

    if not features:
        geometry_source = "county-aggregate"
        features = _county_fallback_features(db, state, scores)
        scored_count = len(features)

    max_revenue = max((f["properties"].get("expected_revenue") or 0) for f in features) if features else 1
    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "state": state,
            "count": len(features),
            "scored_count": scored_count,
            "max_revenue": max_revenue,
            "geometry_source": geometry_source,
        },
    }


@lru_cache(maxsize=64)
def _state_metro_features(state: str) -> tuple:
    """Per-state ZCTAs pre-assigned to their metro (CBSA), with geometry pre-rounded.

    Computing each ZCTA centroid, finding its nearest CBSA, and rounding its geometry is the
    expensive part of a metro heatmap build. This is identical for every metro in the same
    state, so caching it per state means only the first metro in a state pays that cost;
    subsequent metros are a cheap filter. Returns a tuple of (zip_code, cbsa_code, geometry).
    """
    source = load_state_zcta_geojson(state)
    if not source or not source.get("features"):
        return tuple()
    out: list[tuple[str, str, dict | None]] = []
    for feature in source["features"]:
        props = feature.get("properties") or {}
        zip_code = str(
            props.get("ZCTA5CE20") or props.get("GEOID20") or props.get("ZCTA5") or props.get("zip") or ""
        ).zfill(5)
        if len(zip_code) != 5:
            continue
        geometry = feature.get("geometry")
        centroid = geometry_centroid(geometry)
        if not centroid:
            continue
        code = nearest_cbsa(centroid[0], centroid[1])
        if not code:
            continue
        out.append((zip_code, code, _round_geometry(geometry)))
    return tuple(out)


def get_metro_zcta_choropleth(db: Session, upload_id: str | None, cbsa: str) -> dict:
    cbsa = (cbsa or "").strip()
    meta = cbsa_meta(cbsa)
    if not meta:
        return {"type": "FeatureCollection", "features": [], "meta": {"cbsa": cbsa, "count": 0, "error": "unknown cbsa"}}
    scope = f"{DASHBOARD_BUILD_VERSION}:{upload_id or 'all'}:{cbsa}"
    return cached_dashboard("zcta_metro", scope, lambda: _build_metro_zcta_choropleth(db, upload_id, cbsa, meta))


def _build_metro_zcta_choropleth(db: Session, upload_id: str | None, cbsa: str, meta: dict) -> dict:
    states = list(meta.get("states") or [])
    cbsa_name = meta.get("name") or cbsa

    # Scores are computed per state, then filtered to the ZCTAs whose centroid falls in this metro.
    scores: dict[str, dict] = {}
    product_scores: dict[str, dict[str, dict]] = {}
    for st in states:
        scores.update(_attach_product_scores(_zip_scores(db, upload_id, st), _zip_product_scores(db, upload_id, st)))
        product_scores.update(_zip_product_scores(db, upload_id, st))

    features: list[dict] = []
    scored_count = 0
    for st in states:
        for zip_code, code, geometry in _state_metro_features(st):
            if code != cbsa:
                continue
            score = scores.get(zip_code)
            merged_props = _merge_feature_props(zip_code, score, product_scores)
            if score is not None or any(
                p.get("expected_revenue", 0) > 0 for p in product_scores.get(zip_code, {}).values()
            ):
                scored_count += 1
            features.append(
                {
                    "type": "Feature",
                    "id": zip_code,
                    "properties": merged_props,
                    "geometry": geometry,
                }
            )

    max_revenue = max((f["properties"].get("expected_revenue") or 0) for f in features) if features else 1
    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "cbsa": cbsa,
            "cbsa_name": cbsa_name,
            "state": states[0] if states else None,
            "count": len(features),
            "scored_count": scored_count,
            "max_revenue": max_revenue,
            "geometry_source": "zcta500k",
        },
    }
