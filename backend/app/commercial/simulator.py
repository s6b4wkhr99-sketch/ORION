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


def _standing_promotion_bases(product_code: str) -> tuple[float, float]:
    product = product_by_code(product_code) or {}
    default_pct = product.get("default_promotion_pct")
    base_pct = float(default_pct) if default_pct is not None else 0.0
    base_max = float(product.get("max_promotion") or 0)
    return base_pct, base_max


def _layered_promotion_overrides(
    product_code: str,
    *,
    additional_promotion_pct: float | None = None,
    additional_promotion_max: float | None = None,
    promotion_pct: float | None = None,
    max_promotion: float | None = None,
) -> tuple[float | None, float | None]:
    """Apply additional promo layers on catalog standing promo, or honor full overrides."""
    if promotion_pct is not None or max_promotion is not None:
        return promotion_pct, max_promotion

    has_additional = additional_promotion_pct is not None or additional_promotion_max is not None
    if not has_additional:
        return None, None

    base_pct, base_max = _standing_promotion_bases(product_code)
    add_pct = float(additional_promotion_pct or 0)
    add_max = float(additional_promotion_max or 0)
    return round(base_pct + add_pct, 6), round(base_max + add_max, 2)


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
    conversion_rate: float | None = None,
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

    conversion_rate = (
        round(max(0.0000001, min(1.0, float(conversion_rate))), 8)
        if conversion_rate is not None
        else _conversion_estimate(
            float(kpis.get("net_profit_pct") or 0),
            float(kpis.get("promotion_pct") or 0),
            corporate_priority,
        )
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
            + (corporate_priority * 100),
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


def _normalize_target_customers_by_sku(
    target_customers_by_sku: dict[str, int] | list[dict] | None,
) -> dict[str, int] | None:
    if not target_customers_by_sku:
        return None
    if isinstance(target_customers_by_sku, dict):
        return {
            (sku or "").strip(): int(count)
            for sku, count in target_customers_by_sku.items()
            if (sku or "").strip() and int(count) > 0
        } or None
    normalized: dict[str, int] = {}
    for row in target_customers_by_sku:
        sku = str(row.get("sku") or row.get("product") or "").strip()
        count = row.get("count")
        if sku and count is not None and int(count) > 0:
            normalized[sku] = int(count)
    return normalized or None


def _split_target_customers(
    codes: list[str],
    *,
    target_customers: int,
    target_customers_by_sku: dict[str, int] | None,
) -> tuple[list[int], bool]:
    """Return per-SKU target counts. Uses upload mix when provided, else even split."""
    if target_customers_by_sku:
        split = [int(target_customers_by_sku.get(code, 0)) for code in codes]
        if any(count > 0 for count in split):
            return split, True

    n = len(codes)
    base_target = target_customers // n
    split = [base_target] * n
    split[0] += target_customers - sum(split)
    return split, False


def _split_inventory_units(
    codes: list[str],
    *,
    inventory_units: int | None,
    target_split: list[int],
    use_target_mix: bool,
) -> list[int | None]:
    if inventory_units is None or inventory_units < 0:
        return [None] * len(codes)

    n = len(codes)
    if not use_target_mix:
        base_inv = inventory_units // n
        split = [base_inv] * n
        split[0] += inventory_units - sum(split)
        return split

    total_targets = sum(target_split)
    if total_targets <= 0:
        base_inv = inventory_units // n
        split = [base_inv] * n
        split[0] += inventory_units - sum(split)
        return split

    split: list[int] = []
    allocated = 0
    for idx, target in enumerate(target_split):
        if idx == n - 1:
            split.append(max(0, inventory_units - allocated))
        else:
            share = int(inventory_units * target / total_targets)
            split.append(share)
            allocated += share
    return split


def simulate_commercial_multi(
    product_codes: list[str],
    *,
    target_customers: int = 1000,
    target_customers_by_sku: dict[str, int] | list[dict] | None = None,
    selling_price: float | None = None,
    promotion_pct: float | None = None,
    max_promotion: float | None = None,
    additional_promotion_pct: float | None = None,
    additional_promotion_max: float | None = None,
    promo_code: str | None = None,
    le_frame_incentive_rate: float | None = None,
    corporate_priority: float = 0.5,
    inventory_units: int | None = None,
    conversion_rate: float | None = None,
) -> dict:
    """Simulate one or more SKUs; aggregate KPIs across per-SKU targets."""
    codes: list[str] = []
    for code in product_codes:
        cleaned = (code or "").strip()
        if cleaned and cleaned not in codes:
            codes.append(cleaned)
    if not codes:
        raise ValueError("At least one product SKU is required.")

    sku_targets = _normalize_target_customers_by_sku(target_customers_by_sku)

    if len(codes) == 1:
        single_target = int(sku_targets.get(codes[0], 0)) if sku_targets else target_customers
        sku_pct, sku_max = _layered_promotion_overrides(
            codes[0],
            additional_promotion_pct=additional_promotion_pct,
            additional_promotion_max=additional_promotion_max,
            promotion_pct=promotion_pct,
            max_promotion=max_promotion,
        )
        single = simulate_commercial_scenario(
            product_code=codes[0],
            target_customers=single_target,
            selling_price=selling_price,
            promotion_pct=sku_pct,
            max_promotion=sku_max,
            promo_code=promo_code,
            le_frame_incentive_rate=le_frame_incentive_rate,
            corporate_priority=corporate_priority,
            inventory_units=inventory_units,
            conversion_rate=conversion_rate,
        )
        single["products"] = codes
        single["main_product"] = codes[0]
        single["multi_sku"] = False
        single["by_product"] = [_product_slice(single)]
        return single

    if selling_price is not None:
        # Per-SKU catalog pricing applies when multiple SKUs are selected.
        selling_price = None

    if promotion_pct is not None or max_promotion is not None:
        # Legacy full overrides are single-SKU only; ignore for multi and use layered additional promo.
        promotion_pct = None
        max_promotion = None

    n = len(codes)
    target_split, using_target_mix = _split_target_customers(
        codes,
        target_customers=target_customers,
        target_customers_by_sku=sku_targets,
    )
    aggregate_target_customers = sum(target_split) if using_target_mix else target_customers
    inventory_split = _split_inventory_units(
        codes,
        inventory_units=inventory_units,
        target_split=target_split,
        use_target_mix=using_target_mix,
    )

    by_product = []
    for idx, code in enumerate(codes):
        sku_pct, sku_max = _layered_promotion_overrides(
            code,
            additional_promotion_pct=additional_promotion_pct,
            additional_promotion_max=additional_promotion_max,
        )
        by_product.append(
            simulate_commercial_scenario(
                product_code=code,
                target_customers=target_split[idx],
                promotion_pct=sku_pct,
                max_promotion=sku_max,
                le_frame_incentive_rate=le_frame_incentive_rate,
                corporate_priority=corporate_priority,
                inventory_units=inventory_split[idx],
                conversion_rate=conversion_rate,
            )
        )

    total_effective = sum(r["effective_customers"] for r in by_product)
    total_orders = sum(r["expected_orders"] for r in by_product)
    total_revenue = round(sum(r["revenue_forecast"] for r in by_product), 2)
    total_profit = round(sum(r["net_profit"] for r in by_product), 2)
    total_le_frame = round(sum(r["le_frame_revenue"] for r in by_product), 2)
    if conversion_rate is not None:
        aggregate_conversion = round(max(0.0000001, min(1.0, float(conversion_rate))), 8)
    else:
        aggregate_conversion = round(total_orders / total_effective, 6) if total_effective else 0.0
    weighted_score = round(
        sum(r["opportunity_score"] * r["revenue_forecast"] for r in by_product) / max(total_revenue, 1),
        1,
    )

    promo_codes = {r.get("promo_code") for r in by_product if r.get("promo_code")}
    promo_code_out = promo_codes.pop() if len(promo_codes) == 1 else ("Mixed" if promo_codes else None)

    return {
        "simulation": True,
        "multi_sku": True,
        "products": codes,
        "main_product": codes[0],
        "product": ", ".join(codes),
        "target_customers": aggregate_target_customers,
        "effective_customers": total_effective,
        "inventory_units": inventory_units,
        "corporate_priority": corporate_priority,
        "opportunity_score": weighted_score,
        "conversion_prediction": aggregate_conversion,
        "expected_orders": round(total_orders, 2),
        "revenue_forecast": total_revenue,
        "net_profit": total_profit,
        "le_frame_revenue": total_le_frame,
        "recommended_sku": ", ".join(codes),
        "recommended_promotion": round(
            sum(r["recommended_promotion"] for r in by_product) / n,
            2,
        ),
        "promo_code": promo_code_out,
        "capped_promotion": any(r["capped_promotion"] for r in by_product),
        "recommended_lifestyle": "Mixed" if len({r.get("recommended_lifestyle") for r in by_product}) > 1 else by_product[0].get("recommended_lifestyle"),
        "by_product": [_product_slice(r) for r in by_product],
    }


def _product_slice(result: dict) -> dict:
    return {
        "product": result.get("product"),
        "target_customers": result.get("target_customers"),
        "effective_customers": result.get("effective_customers"),
        "opportunity_score": result.get("opportunity_score"),
        "conversion_prediction": result.get("conversion_prediction"),
        "expected_orders": result.get("expected_orders"),
        "revenue_forecast": result.get("revenue_forecast"),
        "net_profit": result.get("net_profit"),
        "le_frame_revenue": result.get("le_frame_revenue"),
        "recommended_promotion": result.get("recommended_promotion"),
        "promo_code": result.get("promo_code"),
        "capped_promotion": result.get("capped_promotion"),
        "recommended_lifestyle": result.get("recommended_lifestyle"),
    }
