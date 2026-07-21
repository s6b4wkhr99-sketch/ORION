"""Projected standing-promo demand — shared by Opportunity Radar and Promotion Coverage."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.scale import UploadRollup
from app.intelligence.ceragem_rules import parse_ceragem_axis, parse_ceragem_tier
from app.commercial.promotion_policy import is_promotion_active, standing_promo_product_order
from app.reference.registry import (
    ACTIVE_PRODUCT_CODES,
    PRODUCT_CATALOG,
    PRODUCT_GROSS_SALES,
)

# Promo SKUs with thin direct recommendation volume inherit demand from adjacent line donors.
STANDING_PROMO_DEMAND_DONORS: dict[str, list[tuple[str, float]]] = {
    "Master V6": [("Master V7", 0.45), ("Master V9", 0.12)],
    "Master V5": [("Master S4", 0.50), ("Master V7", 0.22)],
    "Master S4": [("Pause M4", 0.38), ("Master V5", 0.15)],
    "Pause M6s": [("Pause M6", 0.88), ("Pause M4", 0.22)],
    "Pause M10": [("Master V9", 0.35), ("Master V7", 0.25), ("Pause M6", 0.40), ("Pause M6s", 0.35)],
}

STANDING_PROMO_OUTREACH_MAP: dict[str, str] = {
    "Master V9": "Master V6",
    "Master V7": "Master V6",
    "Master S4": "Master S4",
    "Pause M4": "Master S4",
    "Pause M6": "Pause M10",
    "Pause M6s": "Pause M10",
}


def product_metrics_keys(recommended_product: str) -> tuple[str, ...]:
    """Keys that receive credit for a BD recommendation (direct + standing-promo outreach)."""
    product = (recommended_product or "").strip()
    if not product:
        return tuple()
    outreach = STANDING_PROMO_OUTREACH_MAP.get(product)
    if outreach and outreach != product:
        return (product, outreach)
    return (product,)


def accumulate_product_metrics(
    bucket: dict[str, dict],
    recommended_product: str,
    *,
    customers: int,
    revenue: float,
    orders: float = 0.0,
) -> None:
    """Roll recommended-product counts into direct + outreach SKU buckets."""
    for key in product_metrics_keys(recommended_product):
        row = bucket.setdefault(
            key,
            {"expected_revenue": 0.0, "target_customers": 0, "expected_orders": 0.0},
        )
        row["target_customers"] += int(customers or 0)
        row["expected_revenue"] = round(float(row["expected_revenue"]) + float(revenue or 0), 2)
        row["expected_orders"] = round(float(row.get("expected_orders") or 0) + float(orders or 0), 2)


def accumulate_product_rollups(
    bucket: dict[str, dict],
    recommended_product: str,
    *,
    customers: int,
    revenue: float,
    orders: float = 0.0,
) -> None:
    """Dashboard rollup variant (customers / revenue / orders field names)."""
    for key in product_metrics_keys(recommended_product):
        row = bucket.setdefault(key, {"customers": 0, "revenue": 0.0, "orders": 0.0})
        row["customers"] += int(customers or 0)
        row["revenue"] = round(float(row["revenue"]) + float(revenue or 0), 2)
        row["orders"] = round(float(row["orders"]) + float(orders or 0), 2)

# Outreach conversion nudge only — BD recommendations stay in Rule-065.
STANDING_PROMO_CONVERSION_BIAS: dict[str, float] = {
    "Master V6": 1.12,
    "Master V5": 1.10,
    "Master S4": 1.18,
    "Pause M6s": 1.08,
    "Pause M10": 1.15,
}

STANDING_PROMO_SEGMENT_FIT: dict[str, dict[str, float]] = {
    "Master V6": {
        "Mid-High + Pain Index": 1.0,
        "Mid-High + Wellness": 0.88,
        "High + Pain Index": 0.92,
        "Mid-Low + Pain Index": 0.62,
        "Mid-Low + Wellness": 0.42,
        "High + Wellness": 0.35,
    },
    "Master V5": {
        "Mid-Low + Pain Index": 1.0,
        "Mid-Low + Wellness": 0.82,
        "Mid-High + Pain Index": 0.88,
        "Mid-High + Wellness": 0.55,
        "High + Pain Index": 0.58,
    },
    "Master S4": {
        "Mid-Low + Wellness": 0.95,
        "Mid-Low + Pain Index": 0.82,
        "Mid-High + Wellness": 0.55,
        "Mid-High + Pain Index": 0.72,
    },
    "Pause M10": {
        "High + Wellness": 1.0,
        "Mid-High + Wellness": 0.48,
    },
    "Pause M6s": {
        "Mid-Low + Wellness": 0.9,
        "Mid-Low + Pain Index": 0.78,
        "Mid-High + Wellness": 0.52,
    },
}

_LEGACY_PRODUCT_REMAP = {
    "Pause M2": "Pause M6",
    "MediSpa / Cellunic": "Master S4",
    "Pause S4": "Master S4",
}


def merge_standing_promo_product_rows(product_rows: list[dict]) -> list[dict]:
    """Collapse legacy Pause S4 / Master V4 keys into Master S4 for promo dashboards."""
    from app.reference.registry import normalize_product_code

    merged: dict[str, dict] = {}
    for row in product_rows:
        raw = row.get("product")
        product = normalize_product_code(str(raw) if raw else "")
        if not product:
            continue
        bucket = merged.setdefault(
            product,
            {
                "product": product,
                "customers": 0,
                "revenue": 0.0,
                "orders": 0.0,
                "share_pct": float(row.get("share_pct") or 0),
                "projected": bool(row.get("projected")),
            },
        )
        bucket["customers"] += int(row.get("customers") or 0)
        bucket["revenue"] = round(float(bucket["revenue"]) + float(row.get("revenue") or 0), 2)
        bucket["orders"] = round(float(bucket.get("orders") or 0) + float(row.get("orders") or 0), 2)
        bucket["projected"] = bucket["projected"] or bool(row.get("projected"))
    total_revenue = sum(float(r["revenue"]) for r in merged.values())
    for bucket in merged.values():
        rev = float(bucket["revenue"])
        bucket["share_pct"] = round(rev / total_revenue * 100, 1) if total_revenue else 0.0
    return sorted(merged.values(), key=lambda r: -float(r["revenue"]))


def _normalize_product(product: str | None) -> str:
    from app.reference.registry import normalize_product_code

    code = normalize_product_code((product or "Unknown").strip())
    if code in ACTIVE_PRODUCT_CODES:
        return code
    if code in _LEGACY_PRODUCT_REMAP:
        return _LEGACY_PRODUCT_REMAP[code]
    discontinued = {
        p["code"]: "Pause M6"
        for p in PRODUCT_CATALOG
        if not p.get("active", True) and p["family"] in {"Master", "Pause"}
    }
    return discontinued.get(code, "Pause M6")


def _state_codes_with_product_rollups(db: Session, upload_id) -> list[str]:
    q = db.query(UploadRollup.scope).filter(
        UploadRollup.dimension == "product",
        UploadRollup.scope.isnot(None),
        UploadRollup.scope != "*",
        UploadRollup.scope != "Unknown",
    )
    if upload_id:
        q = q.filter(UploadRollup.upload_id == upload_id)
    return sorted({row[0] for row in q.distinct().all() if row[0]})


def _product_breakdown_by_states(db: Session, upload_id, state_codes: list[str]) -> list[dict]:
    """Per-state product rollups for standing-promo demand projection."""
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
                "product": _normalize_product(str(key)),
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
            "product": _normalize_product(str(key)),
            "customers": int(count or 0),
            "orders": float(orders or 0),
            "revenue": float(revenue or 0),
        }
        for scope, key, count, orders, revenue in rows
    ]


def _product_cells_by_state(db: Session, upload_id, state_codes: list[str]) -> dict[tuple[str, str], dict]:
    cells: dict[tuple[str, str], dict] = {}
    for row in _product_breakdown_by_states(db, upload_id, state_codes):
        if int(row.get("customers") or 0) <= 0:
            continue
        cells[(row["state"], row["product"])] = row
    return cells


def pad_geo_product_rows(
    product: str,
    ranked: list[dict],
    donor_buckets: dict[str, list[dict]],
    *,
    geo_field: str,
    limit: int,
) -> list[dict]:
    """Fill thin promo SKU geo lists from donor rows (scatter charts — not choropleth maps)."""
    if len(ranked) >= limit:
        return [{**row, "product": product, "top_product": product} for row in ranked[:limit]]

    seen = {str(row.get(geo_field) or "") for row in ranked}
    padded = list(ranked)
    for donor_product, _weight in STANDING_PROMO_DEMAND_DONORS.get(product, []):
        for row in donor_buckets.get(donor_product, []):
            geo = str(row.get(geo_field) or "")
            if not geo or geo in seen:
                continue
            padded.append({**row, "product": product, "top_product": product})
            seen.add(geo)
            if len(padded) >= limit:
                return [{**row, "product": product, "top_product": product} for row in padded[:limit]]
    return [{**row, "product": product, "top_product": product} for row in padded]


def synthesize_standing_promo_cells(
    cells: dict[tuple[str, str], dict],
    state_codes: list[str],
) -> None:
    """Fill promo-target SKUs from donor product demand within each state (in-place, all states)."""
    for target, donors in STANDING_PROMO_DEMAND_DONORS.items():
        for state in state_codes:
            existing = cells.get((state, target))
            if existing and int(existing.get("customers") or 0) > 0:
                continue

            customers = 0
            orders = 0.0
            revenue = 0.0
            for donor, weight in donors:
                donor_row = cells.get((state, donor))
                if not donor_row:
                    continue
                donor_customers = int(donor_row.get("customers") or 0)
                if donor_customers <= 0:
                    continue
                projected = max(1, int(round(donor_customers * weight)))
                customers += projected
                orders += float(donor_row.get("orders") or 0) * weight
                revenue += float(donor_row.get("revenue") or 0) * weight

            if customers > 0 and revenue > 0:
                cells[(state, target)] = {
                    "state": state,
                    "product": target,
                    "customers": customers,
                    "orders": orders,
                    "revenue": revenue,
                    "synthetic": True,
                }


def standing_promo_outreach_product(
    product: str | None,
    *,
    purchase_power: str | None = None,
    ceragem_segment: str | None = None,
) -> str | None:
    """Map intelligence SKU to standing-promo outreach SKU (segment + post-promo price aware)."""
    from app.intelligence.promo_price_response import resolve_promo_price_response

    if not product:
        return product
    code = product.strip()
    active_promos = set(standing_promo_product_order())
    pp = (purchase_power or "").strip()
    segment = (ceragem_segment or "").strip()

    if not pp and not segment:
        if code in active_promos and is_promotion_active(code):
            return code
        return STANDING_PROMO_OUTREACH_MAP.get(code, code)

    if code in active_promos and is_promotion_active(code):
        candidate = code
    elif code in active_promos:
        candidate = code
    else:
        candidate = STANDING_PROMO_OUTREACH_MAP.get(code, code)

    tier = parse_ceragem_tier(segment)
    axis = parse_ceragem_axis(segment)

    if tier in {"Mid-Low+", "Low+"} or pp in {"Low", "Medium"}:
        if candidate in {"Master V6", "Master V7", "Master V9", "Master S4", "Master V4"}:
            candidate = "Master V5" if axis == "Pain Index" or pp == "Low" else "Master V6"
    elif tier == "Mid-High+" and axis == "Wellness" and pp in {"Low", "Medium"}:
        candidate = "Master V6"
    elif tier == "High+" and axis == "Wellness" and pp == "High":
        candidate = "Pause M10"
    elif candidate == "Pause M10" and pp in {"Low", "Medium"}:
        candidate = "Pause M6s" if tier in {"Mid-Low+", "Low+"} else "Master V6"
    elif candidate not in active_promos:
        candidate = STANDING_PROMO_OUTREACH_MAP.get(candidate, candidate)
    elif not is_promotion_active(candidate):
        candidate = code

    response = resolve_promo_price_response(
        candidate,
        purchase_power_category=pp or None,
        ceragem_segment=segment or None,
    )
    if response.accessible and response.outreach_sku in active_promos:
        return response.outreach_sku
    return candidate if candidate in active_promos else code


def _pp_accessibility_factor(gross_sales: float, pp_bands: dict[str, float]) -> float:
    """How much of the base can afford this promo price (PP High/Medium/Low %)."""
    high = float(pp_bands.get("high") or 0)
    medium = float(pp_bands.get("medium") or 0)
    low = float(pp_bands.get("low") or 0)
    if gross_sales >= 9000:
        return (high * 1.0 + medium * 0.12 + low * 0.02) / 100.0
    if gross_sales >= 6000:
        return (high * 0.95 + medium * 0.72 + low * 0.18) / 100.0
    if gross_sales >= 4500:
        return (high * 0.9 + medium * 0.84 + low * 0.52) / 100.0
    return (high * 0.85 + medium * 0.88 + low * 0.78) / 100.0


def _segment_alignment_factor(product: str, segment_rows: list[dict]) -> float:
    fits = STANDING_PROMO_SEGMENT_FIT.get(product, {})
    total = sum(int(row.get("customers") or 0) for row in segment_rows)
    if total <= 0:
        return 0.25
    weighted = sum(
        int(row.get("customers") or 0) * float(fits.get(str(row.get("segment") or ""), 0.2))
        for row in segment_rows
    )
    return weighted / total


def _segment_weighted_conversion(product: str, segment_rows: list[dict]) -> float:
    fits = STANDING_PROMO_SEGMENT_FIT.get(product, {})
    weighted_customers = 0.0
    weighted_orders = 0.0
    for row in segment_rows:
        customers = int(row.get("customers") or 0)
        if customers <= 0:
            continue
        fit = float(fits.get(str(row.get("segment") or ""), 0.2))
        weighted_customers += customers * fit
        weighted_orders += customers * fit * float(row.get("conversion") or 0)
    if weighted_customers <= 0:
        return 0.003
    return weighted_orders / weighted_customers


def _market_alignment_bias(product: str, segment_rows: list[dict]) -> float:
    """Pain-dominant base favors FDA V-series (V6/V5) over Pause M rest line."""
    total = sum(int(row.get("customers") or 0) for row in segment_rows) or 1
    pain_share = sum(
        int(row.get("customers") or 0)
        for row in segment_rows
        if "Pain" in str(row.get("segment") or "")
    ) / total
    if product in {"Master V6", "Master V5"}:
        return 1.0 + pain_share * 0.22
    if product.startswith("Pause M"):
        return max(0.72, 1.0 - pain_share * 0.2)
    return 1.0


def pick_highest_conversion_opportunity(
    db: Session,
    upload_id,
    product_rows: list[dict],
    segment_rows: list[dict],
    pp_bands: dict[str, float],
    targetable_customers: float = 0,
) -> dict | None:
    """
    Highest Opportunity = standing promo with best conversion-weighted reach.

    Weighs addressable customers by segment fit, post-promo price accessibility (PP),
    and observed segment conversion — not raw intelligence revenue (M10 bias).
    """
    base_map = {row["product"]: row for row in build_standing_promo_opportunity_rows(db, upload_id, product_rows)}
    segment_total = sum(int(row.get("customers") or 0) for row in segment_rows)
    if not base_map and segment_total <= 0:
        return None

    scored: list[dict] = []
    for product in standing_promo_product_order():
        row = base_map.get(product, {"product": product, "customers": 0, "revenue": 0.0, "projected": True})
        gross_sales = float(PRODUCT_GROSS_SALES.get(product) or 0)
        customers = int(row.get("customers") or 0)
        segment_fit = _segment_alignment_factor(product, segment_rows)
        pp_fit = _pp_accessibility_factor(gross_sales, pp_bands)
        conversion = _segment_weighted_conversion(product, segment_rows)
        bias = float(STANDING_PROMO_CONVERSION_BIAS.get(product, 1.0)) * _market_alignment_bias(product, segment_rows)
        segment_derived = int(round(segment_total * segment_fit * pp_fit * 0.12)) if segment_total > 0 else 0
        catalog_addressable = int(round(customers * segment_fit * pp_fit)) if customers > 0 else 0
        addressable = max(segment_derived, catalog_addressable)
        expected_orders = addressable * conversion * bias
        expected_revenue = round(expected_orders * gross_sales, 2)
        scored.append(
            {
                **row,
                "segment_fit": round(segment_fit, 4),
                "pp_accessibility": round(pp_fit, 4),
                "weighted_conversion": round(conversion, 6),
                "addressable_customers": int(round(addressable)),
                "expected_orders": round(expected_orders, 2),
                "conversion_weighted_revenue": expected_revenue,
            }
        )

    best = max(scored, key=lambda item: float(item.get("conversion_weighted_revenue") or 0))
    denominator = max(int(targetable_customers or 0), 1)
    return {
        "product": best["product"],
        "revenue": best["conversion_weighted_revenue"],
        "raw_revenue": best.get("revenue"),
        "customers": best["addressable_customers"],
        "customer_share_pct": round(best["addressable_customers"] / denominator * 100, 1),
        "share_pct": best.get("share_pct"),
        "projected": bool(best.get("projected")),
        "segment_fit": best["segment_fit"],
        "pp_accessibility": best["pp_accessibility"],
        "weighted_conversion": best["weighted_conversion"],
        "kpi_basis": "conversion_weighted_standing_promo",
    }


def _aggregate_standing_promo_cells(db: Session, upload_id) -> dict[str, dict]:
    if not hasattr(db, "query"):
        return {}
    state_codes = _state_codes_with_product_rollups(db, upload_id)
    if not state_codes:
        return {}

    cells = _product_cells_by_state(db, upload_id, state_codes)
    synthesize_standing_promo_cells(cells, state_codes)

    totals: dict[str, dict] = defaultdict(lambda: {"customers": 0, "revenue": 0.0, "projected": False})
    for (_state, product), row in cells.items():
        if product not in set(standing_promo_product_order()):
            continue
        totals[product]["customers"] += int(row.get("customers") or 0)
        totals[product]["revenue"] += float(row.get("revenue") or 0)
        if row.get("synthetic"):
            totals[product]["projected"] = True
    return dict(totals)


def project_standing_promo_customers(db: Session, upload_id) -> dict[str, int]:
    """Sum projected addressable customers per standing-promo SKU (state rollups + donor synthesis)."""
    totals = _aggregate_standing_promo_cells(db, upload_id)
    return {product: int(values["customers"]) for product, values in totals.items()}


def project_standing_promo_distribution(db: Session, upload_id) -> list[dict]:
    """Per standing-promo SKU addressable customers and revenue after donor synthesis."""
    totals = _aggregate_standing_promo_cells(db, upload_id)
    if not totals:
        return []

    ranked = sorted(totals.items(), key=lambda item: -item[1]["revenue"])
    total_revenue = sum(values["revenue"] for _, values in ranked)
    return [
        {
            "product": product,
            "customers": int(values["customers"]),
            "revenue": round(float(values["revenue"]), 2),
            "share_pct": round(values["revenue"] / total_revenue * 100, 1) if total_revenue else 0.0,
            "projected": bool(values["projected"]),
        }
        for product, values in ranked
    ]


def build_standing_promo_opportunity_rows(
    db: Session,
    upload_id,
    product_rows: list[dict],
) -> list[dict]:
    """Merge actual recommendation totals with projected standing-promo addressable demand."""
    product_rows = merge_standing_promo_product_rows(product_rows)
    projected = {row["product"]: row for row in project_standing_promo_distribution(db, upload_id)}
    actual = {row.get("product"): row for row in product_rows if row.get("product")}
    rows: list[dict] = []
    for product_code in standing_promo_product_order():
        actual_row = actual.get(product_code, {})
        projected_row = projected.get(product_code, {})
        customers = max(int(actual_row.get("customers") or 0), int(projected_row.get("customers") or 0))
        revenue = max(float(actual_row.get("revenue") or 0), float(projected_row.get("revenue") or 0))
        if customers <= 0 and revenue <= 0:
            continue
        rows.append(
            {
                "product": product_code,
                "customers": customers,
                "revenue": round(revenue, 2),
                "share_pct": projected_row.get("share_pct") or actual_row.get("share_pct"),
                "projected": bool(projected_row.get("projected")) and int(actual_row.get("customers") or 0) == 0,
            }
        )
    return sorted(rows, key=lambda row: -float(row.get("revenue") or 0))
