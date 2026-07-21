"""Commercial Simulator — what-if pricing without modifying production data."""

from __future__ import annotations

from copy import deepcopy

from app.commercial.catalog import active_products, product_by_code
from app.commercial.engine import CERAGEM_UNIT_COST_RATIO, build_commercial_kpis
from app.reference.registry import LE_FRAME_COMMISSION_RATE


def _apply_overrides(product: dict, overrides: dict) -> dict:
    patched = deepcopy(product)
    if overrides.get("selling_price") is not None:
        patched["selling_price"] = float(overrides["selling_price"])
        patched["gross_sales"] = float(overrides.get("gross_sales") or overrides["selling_price"])
    if overrides.get("max_promotion") is not None:
        patched["max_promotion"] = float(overrides["max_promotion"])
    if overrides.get("promotion_pct") is not None:
        patched["default_promotion_pct"] = float(overrides["promotion_pct"])
    if overrides.get("promo_code") is not None:
        patched["promo_code"] = overrides["promo_code"] or None
    if overrides.get("le_frame_incentive_rate") is not None:
        rate = float(overrides["le_frame_incentive_rate"])
        gross = float(patched.get("gross_sales") or patched.get("selling_price") or 0)
        patched["le_frame_incentive"] = round(gross * rate, 2)
    return patched


def _conversion_estimate(net_profit_pct: float, promotion_pct: float, corporate_priority: float = 0.5) -> float:
    base = 0.0028
    margin_lift = max(-0.001, min(0.002, net_profit_pct * 0.004))
    promo_lift = max(-0.0015, min(0.003, promotion_pct * 0.006))
    priority_lift = (corporate_priority - 0.5) * 0.001
    return round(max(0.0005, min(0.02, base + margin_lift + promo_lift + priority_lift)), 6)


def simulate_commercial_scenario(
    *,
    product_code: str,
    target_customers: int = 1000,
    selling_price: float | None = None,
    promotion_pct: float | None = None,
    max_promotion: float | None = None,
    promo_code: str | None = None,
    le_frame_incentive_rate: float | None = None,
    corporate_priority: float = 0.5,
    inventory_units: int | None = None,
) -> dict:
    """Return temporary simulation results — never writes to production."""
    base = product_by_code(product_code)
    if base is None:
        active = [p["code"] for p in active_products()]
        raise ValueError(f"Unknown product '{product_code}'. Active SKUs: {', '.join(active)}")

    overrides = {
        "selling_price": selling_price,
        "promotion_pct": promotion_pct,
        "max_promotion": max_promotion,
        "promo_code": promo_code,
        "le_frame_incentive_rate": le_frame_incentive_rate,
    }
    product = _apply_overrides(base, overrides)

    selling = float(product.get("selling_price") or product.get("msrp") or 0)
    default_pct = product.get("default_promotion_pct")
    if promotion_pct is not None:
        proposed_promo = round(selling * float(promotion_pct), 2)
    elif default_pct is not None:
        proposed_promo = round(selling * float(default_pct), 2)
    else:
        proposed_promo = float(product.get("max_promotion") or 0)

    max_allowed = float(product.get("max_promotion") or 0)
    promotion_amount = round(min(max(0.0, proposed_promo), max_allowed), 2)
    capped_flag = proposed_promo > max_allowed

    kpis = build_commercial_kpis(product_code, promotion_amount)
    if le_frame_incentive_rate is not None:
        kpis["le_frame_incentive_rate"] = float(le_frame_incentive_rate)
        kpis["le_frame_incentive_unit"] = round(kpis["gross_sales"] * float(le_frame_incentive_rate), 2)

    conversion_rate = _conversion_estimate(
        float(kpis.get("net_profit_pct") or 0),
        float(kpis.get("promotion_pct") or 0),
        corporate_priority,
    )
    effective_customers = target_customers
    if inventory_units is not None and inventory_units >= 0:
        effective_customers = min(target_customers, inventory_units)

    expected_orders = round(effective_customers * conversion_rate, 2)
    expected_revenue = round(expected_orders * float(kpis.get("customer_payment") or selling), 2)
    le_frame_revenue = round(expected_orders * float(kpis.get("le_frame_incentive_unit") or 0), 2)
    net_profit_total = round(expected_orders * float(kpis.get("net_profit") or 0), 2)

    opportunity_score = round(
        min(
            99.0,
            (float(kpis.get("net_profit_pct") or 0) * 40)
            + (conversion_rate * 10000)
            + (corporate_priority * 20),
        ),
        1,
    )

    return {
        "simulation": True,
        "product": product_code,
        "target_customers": target_customers,
        "effective_customers": effective_customers,
        "inventory_units": inventory_units,
        "corporate_priority": corporate_priority,
        "opportunity_score": opportunity_score,
        "conversion_prediction": conversion_rate,
        "expected_orders": expected_orders,
        "revenue_forecast": expected_revenue,
        "net_profit": net_profit_total,
        "le_frame_revenue": le_frame_revenue,
        "recommended_sku": product_code,
        "recommended_promotion": promotion_amount,
        "promo_code": kpis.get("promo_code"),
        "commercial_kpis": kpis,
        "capped_promotion": capped_flag,
        "recommended_audience": "Targetable customers matching SKU segment",
        "recommended_state": None,
        "recommended_zip": None,
        "recommended_lifestyle": product.get("segment"),
    }
