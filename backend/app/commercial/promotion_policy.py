"""Runtime-active promotion policy — promos are variable, not always-on.

Promotions can be turned on/off and their code or discount % changed via the published
commercial catalog. Registry ``ACTIVE_STANDING_PROMOTIONS`` is a default seed only;
runtime truth is ``promo_code`` + ``default_promotion_pct`` on each catalog SKU.
"""

from __future__ import annotations

from app.commercial.catalog import active_products, product_by_code
from app.reference.registry import ACTIVE_STANDING_PROMOTION_ORDER, normalize_product_code


def _resolve_product_code(product_code: str | None) -> str:
    return normalize_product_code((product_code or "").strip())


def _promo_meta(product: dict | None) -> dict | None:
    if not product:
        return None
    code = product.get("promo_code")
    if not code:
        return None
    pct = product.get("default_promotion_pct")
    if pct is None or float(pct) <= 0:
        return None
    return {"promo_code": str(code), "default_promotion_pct": float(pct)}


def is_promotion_active(product_code: str | None) -> bool:
    if not product_code:
        return False
    return _promo_meta(product_by_code(_resolve_product_code(product_code))) is not None


def promotion_pct(product_code: str | None) -> float:
    if not product_code:
        return 0.0
    meta = _promo_meta(product_by_code(_resolve_product_code(product_code)))
    return float(meta["default_promotion_pct"]) if meta else 0.0


def promo_code(product_code: str | None) -> str | None:
    if not product_code:
        return None
    meta = _promo_meta(product_by_code(_resolve_product_code(product_code)))
    return str(meta["promo_code"]) if meta else None


def active_promotion_order() -> tuple[str, ...]:
    """Display / rollup order for SKUs that currently carry an active promo."""
    active_codes = {
        p["code"]
        for p in active_products()
        if p.get("code") and is_promotion_active(p["code"])
    }
    ordered = [code for code in ACTIVE_STANDING_PROMOTION_ORDER if code in active_codes]
    extras = sorted(active_codes - set(ordered))
    return tuple(ordered + extras)


def standing_promo_product_order() -> tuple[str, ...]:
    """Active standing-promo SKUs — Master S4 SSOT (legacy Pause S4 never surfaced)."""
    seen: set[str] = set()
    ordered: list[str] = []
    for code in active_promotion_order():
        resolved = _resolve_product_code(code)
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(resolved)
    for code in ACTIVE_STANDING_PROMOTION_ORDER:
        resolved = _resolve_product_code(code)
        if resolved in seen:
            continue
        if is_promotion_active(resolved):
            ordered.append(resolved)
            seen.add(resolved)
    return tuple(ordered)


def build_active_promotion_rows() -> list[dict]:
    rows: list[dict] = []
    for product_code in standing_promo_product_order():
        product = product_by_code(product_code)
        meta = _promo_meta(product)
        if not product or not meta:
            continue
        selling = float(product.get("selling_price") or product.get("gross_sales") or product.get("msrp") or 0)
        rows.append(
            {
                "product": product_code,
                "promo_code": meta["promo_code"],
                "max_promotion": float(product.get("max_promotion") or 0),
                "default_promotion_pct": round(meta["default_promotion_pct"] * 100, 1),
                "selling_price": selling,
                "status": "active",
            }
        )
    return rows
