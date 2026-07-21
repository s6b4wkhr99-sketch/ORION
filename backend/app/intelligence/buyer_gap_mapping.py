"""Buyer purchase → prospect counterpart SKU rules for GAP / model-validation analysis.

These mappings do NOT alter dashboard KPIs, standing promos, or recommendation output.
They only normalize actual purchases before comparing to prospect intelligence.
"""

from __future__ import annotations

import re

from app.intelligence.ceragem_rules import segment_axis_is_pain

# --- Prospect SKU targets ---
V4_DEFAULT_COUNTERPART = "Master S4"
V4_UPTIER_COUNTERPART = "Master V5"
M2_COUNTERPART = "Pause M4"

# Buyer material token → ORION Master / Pause SKU (direct 1:1 except V4/M2).
_DIRECT_PURCHASE_MAP: dict[str, str] = {
    "V5": "Master V5",
    "V6": "Master V6",
    "V7": "Master V7",
    "V9": "Master V9",
    "M4": "Pause M4",
    "M6": "Pause M6",
    "M6S": "Pause M6s",
    "M10": "Pause M10",
}

_V_LINE = frozenset({"Master V9", "Master V7", "Master V6", "Master V5", "Master S4"})
_M_LINE = frozenset({"Pause M10", "Pause M6", "Pause M6s", "Pause M4"})

# PRIZM segments where V4 buyers are compared against V5 (premium / upmarket ladder).
_V5_PRIZM = frozenset(
    {
        "Established Elite",
        "Suburban Sophisticates",
        "Booming with Confidence",
    },
)

# Ceragem segments where V4 buyers map to V5 (V-line mid/premium ladder ahead of S4).
_V5_CERAGEM = frozenset(
    {
        "High+ · Wellness",
        "High+ · Pain Index",
        "Mid-High+ · Wellness",
        "Mid-High+ · Pain Index",
        "Mid+ · Pain Index",
        "Mid-Low+ · Pain Index",
    },
)

_CHAIR_TOKEN_RE = re.compile(r"\b(V[4-9]|M2|M4|M6S?|M10|S4)\b", re.I)


def index_level(value: float | str | None) -> str:
    if value is None:
        return "Low"
    if isinstance(value, str):
        s = value.strip().title()
        if s in {"High", "Medium", "Low"}:
            return s
        try:
            value = float(s)
        except ValueError:
            return "Low"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "Low"
    if v >= 0.75:
        return "High"
    if v >= 0.45:
        return "Medium"
    return "Low"


def parse_purchase_token(material_or_sku: str | None) -> str | None:
    """Extract chair SKU token from legacy/Shopify material text."""
    if not material_or_sku:
        return None
    match = _CHAIR_TOKEN_RE.search(str(material_or_sku).upper())
    if not match:
        return None
    token = match.group(1).upper()
    if token == "S4":
        return "V4"
    if token == "M6S":
        return "M6S"
    return token


def purchase_series(token: str | None) -> str | None:
    if not token:
        return None
    if token.startswith("V"):
        return "V"
    if token.startswith("M"):
        return "M"
    return None


def master_series(sku: str | None) -> str | None:
    if not sku:
        return None
    if sku in _V_LINE or sku.startswith("Master V") or sku == "Master S4":
        return "V"
    if sku in _M_LINE or sku.startswith("Pause M"):
        return "M"
    return None


def direct_purchase_to_master(token: str | None) -> str | None:
    if not token:
        return None
    return _DIRECT_PURCHASE_MAP.get(token.upper())


def is_v4_purchase(material_or_sku: str | None) -> bool:
    return parse_purchase_token(material_or_sku) == "V4"


def is_m2_purchase(material_or_sku: str | None) -> bool:
    return parse_purchase_token(material_or_sku) == "M2"


def v4_prospect_counterpart(
    *,
    ceragem_segment: str | None,
    prizm_proxy_segment: str | None,
    purchase_power_index: float | str | None,
    lifestyle_index: float | str | None,
    pain_index: float | str | None = None,
    zip_income_tier: str | None = None,
    premium_zip: bool = False,
    customer_state: str | None = None,
) -> tuple[str, str]:
    """Return (counterpart SKU, rule id). Default Master S4; split to V5 when upmarket."""
    ceragem = (ceragem_segment or "").strip()
    prizm = (prizm_proxy_segment or "").strip()
    pp = index_level(purchase_power_index)
    lifestyle = index_level(lifestyle_index)
    pain = index_level(pain_index)
    state = (customer_state or "").strip().upper()[:2] if customer_state else ""
    zip_tier = (zip_income_tier or "").strip() or (
        "Lower" if pp == "Low" else ("Mid" if pp == "Medium" else "High")
    )

    if prizm in _V5_PRIZM:
        return V4_UPTIER_COUNTERPART, "prizm_premium"
    if ceragem in _V5_CERAGEM:
        return V4_UPTIER_COUNTERPART, "ceragem_v5_ladder"
    if pp == "High":
        return V4_UPTIER_COUNTERPART, "purchase_power_high"
    if lifestyle == "High" and pp in {"High", "Medium"}:
        return V4_UPTIER_COUNTERPART, "lifestyle_high"
    if pain == "High" and segment_axis_is_pain(ceragem):
        return V4_UPTIER_COUNTERPART, "pain_high_axis"
    if zip_tier == "High" and pp in {"High", "Medium"}:
        return V4_UPTIER_COUNTERPART, "affluent_zip"
    if premium_zip and pp != "Low":
        return V4_UPTIER_COUNTERPART, "premium_zip"
    if state in {"CA", "NY", "NJ", "VA", "DC", "WA"} and pp == "Medium" and lifestyle in {"Medium", "High"}:
        return V4_UPTIER_COUNTERPART, "priority_market_mid_pp"

    return V4_DEFAULT_COUNTERPART, "default_s4"


def buyer_compare_sku(
    material_or_sku: str | None,
    *,
    ceragem_segment: str | None = None,
    prizm_proxy_segment: str | None = None,
    purchase_power_index: float | str | None = None,
    lifestyle_index: float | str | None = None,
    pain_index: float | str | None = None,
    zip_income_tier: str | None = None,
    premium_zip: bool = False,
    customer_state: str | None = None,
    recommended_product: str | None = None,
) -> tuple[str | None, str]:
    """Map a buyer line item to the prospect SKU used in GAP hit-rate tests."""
    token = parse_purchase_token(material_or_sku)
    if token == "M2":
        return M2_COUNTERPART, "m2_to_m4"
    if token == "V4":
        sku, rule = v4_prospect_counterpart(
            ceragem_segment=ceragem_segment,
            prizm_proxy_segment=prizm_proxy_segment,
            purchase_power_index=purchase_power_index,
            lifestyle_index=lifestyle_index,
            pain_index=pain_index,
            zip_income_tier=zip_income_tier,
            premium_zip=premium_zip,
            customer_state=customer_state,
        )
        return sku, rule
    direct = direct_purchase_to_master(token)
    if direct:
        return direct, "direct_map"
    return None, "unmapped"
