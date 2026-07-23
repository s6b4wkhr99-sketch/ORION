"""Parse Audience Export CSV and run Commercial Simulator analysis."""

from __future__ import annotations

import csv
import io
import re
from collections import Counter

from app.commercial.catalog import active_products, product_by_code
from app.commercial.simulator import simulate_commercial_scenario

_CAMPAIGN_SKU_RE = re.compile(r"Opportunity\s*[·•]\s*(.+?)\s*[·•]", re.I)
_PRODUCT_HEADERS = (
    "recommended product",
    "target sku",
    "product",
    "sku",
    "main sku",
)
_PROMO_CODE_HEADERS = ("promo code",)
_PROMO_AMOUNT_HEADERS = ("recommended promotion", "promotion", "promo amount")
_CAMPAIGN_NAME_HEADERS = ("campaign name",)
_CAMPAIGN_ID_HEADERS = ("campaign id",)
_STATE_HEADERS = ("state", "st")


def _normalize_header(value: str) -> str:
    return (value or "").strip().lower()


def _pick_column(fieldnames: list[str], candidates: tuple[str, ...]) -> str | None:
    normalized = {_normalize_header(name): name for name in fieldnames}
    for cand in candidates:
        if cand in normalized:
            return normalized[cand]
    for name in fieldnames:
        low = _normalize_header(name)
        for cand in candidates:
            if cand in low:
                return name
    return None


def _parse_money(value: str | None) -> float | None:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", str(value).strip())
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _mode(values: list[str]) -> str | None:
    items = [v.strip() for v in values if v and str(v).strip()]
    if not items:
        return None
    return Counter(items).most_common(1)[0][0]


def _resolve_product_code(
    rows: list[dict[str, str]],
    product_col: str | None,
    campaign_name: str | None,
) -> str:
    active_codes = {p["code"] for p in active_products()}
    if product_col:
        counts = Counter(
            (rows[i].get(product_col) or "").strip()
            for i in range(len(rows))
            if (rows[i].get(product_col) or "").strip()
        )
        for candidate, _ in counts.most_common():
            if candidate in active_codes:
                return candidate

    if campaign_name:
        match = _CAMPAIGN_SKU_RE.search(campaign_name)
        if match:
            candidate = match.group(1).strip()
            if candidate in active_codes:
                return candidate

    raise ValueError(
        "Could not determine campaign SKU. Export must include Recommended Product "
        "or an Opportunity-style Campaign Name (e.g. Opportunity · Master V7 · …)."
    )


def parse_audience_export_csv(content: bytes) -> dict:
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV has no header row.")

    rows = [dict(row) for row in reader if any((v or "").strip() for v in row.values())]
    if not rows:
        raise ValueError("CSV contains no data rows.")

    product_col = _pick_column(reader.fieldnames, _PRODUCT_HEADERS)
    promo_code_col = _pick_column(reader.fieldnames, _PROMO_CODE_HEADERS)
    promo_amt_col = _pick_column(reader.fieldnames, _PROMO_AMOUNT_HEADERS)
    campaign_name_col = _pick_column(reader.fieldnames, _CAMPAIGN_NAME_HEADERS)
    campaign_id_col = _pick_column(reader.fieldnames, _CAMPAIGN_ID_HEADERS)
    state_col = _pick_column(reader.fieldnames, _STATE_HEADERS)

    campaign_name = rows[0].get(campaign_name_col or "", "").strip() if campaign_name_col else None
    campaign_id = rows[0].get(campaign_id_col or "", "").strip() if campaign_id_col else None

    product_code = _resolve_product_code(rows, product_col, campaign_name)
    promo_code = _mode([row.get(promo_code_col or "", "") for row in rows]) if promo_code_col else None

    promo_amounts = []
    if promo_amt_col:
        for row in rows:
            amount = _parse_money(row.get(promo_amt_col))
            if amount is not None:
                promo_amounts.append(amount)
    avg_promotion = round(sum(promo_amounts) / len(promo_amounts), 2) if promo_amounts else None

    promotion_pct = None
    if avg_promotion is not None:
        catalog = product_by_code(product_code) or {}
        selling = float(catalog.get("selling_price") or catalog.get("msrp") or 0)
        if selling > 0:
            promotion_pct = round(avg_promotion / selling, 4)

    state_counts: Counter[str] = Counter()
    if state_col:
        for row in rows:
            state = (row.get(state_col) or "").strip().upper()
            if state:
                state_counts[state] += 1

    sku_counts: Counter[str] = Counter()
    if product_col:
        for row in rows:
            sku = (row.get(product_col) or "").strip()
            if sku:
                sku_counts[sku] += 1

    promo_code_counts: Counter[str] = Counter()
    if promo_code_col:
        for row in rows:
            code = (row.get(promo_code_col) or "").strip()
            if code:
                promo_code_counts[code] += 1

    avg_selling_price = _weighted_avg_selling_price(sku_counts, product_code)

    return {
        "target_customers": len(rows),
        "product": product_code,
        "campaign_name": campaign_name,
        "campaign_id": campaign_id,
        "promo_code": promo_code,
        "avg_promotion": avg_promotion,
        "promotion_pct": promotion_pct,
        "avg_selling_price": avg_selling_price,
        "top_states": [{"state": s, "count": n} for s, n in state_counts.most_common(5)],
        "sku_mix": [{"sku": s, "count": n} for s, n in sorted(sku_counts.items(), key=lambda item: (-item[1], item[0]))],
        "promo_code_mix": [
            {"promo_code": code, "count": n}
            for code, n in sorted(promo_code_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "file_rows": len(rows),
    }


def _catalog_selling_price(product_code: str) -> float:
    catalog = product_by_code(product_code) or {}
    return float(catalog.get("selling_price") or catalog.get("msrp") or 0)


def _weighted_avg_selling_price(sku_counts: Counter[str], fallback_product: str) -> float | None:
    weighted = 0.0
    total = 0
    for sku, count in sku_counts.items():
        price = _catalog_selling_price(sku)
        if price > 0 and count > 0:
            weighted += price * count
            total += count
    if total > 0:
        return round(weighted / total, 2)
    fallback_price = _catalog_selling_price(fallback_product)
    return round(fallback_price, 2) if fallback_price > 0 else None


def analyze_audience_export_csv(
    content: bytes,
    *,
    corporate_priority: float = 0.5,
    le_frame_incentive_rate: float | None = 0.15,
    inventory_units: int | None = None,
    selling_price: float | None = None,
    conversion_rate: float | None = None,
) -> dict:
    audience = parse_audience_export_csv(content)
    simulation = simulate_commercial_scenario(
        product_code=audience["product"],
        target_customers=audience["target_customers"],
        selling_price=selling_price,
        promotion_pct=audience.get("promotion_pct"),
        max_promotion=audience.get("avg_promotion"),
        promo_code=audience.get("promo_code"),
        le_frame_incentive_rate=le_frame_incentive_rate,
        corporate_priority=corporate_priority,
        inventory_units=inventory_units,
        conversion_rate=conversion_rate,
    )
    return {"audience": audience, "simulation": simulation}
