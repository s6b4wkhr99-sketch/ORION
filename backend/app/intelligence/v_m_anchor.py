"""V:M sales-mix anchor nudge + migration strength gate."""

from __future__ import annotations

import hashlib

from app.intelligence.ceragem_rules import segment_axis_is_pain
from app.intelligence.product_ladders import _M_LINE_SKUS, _V_LINE_SKUS, is_post_promo_v_accessible
from app.intelligence.promotion_policy_constants import (
    MIGRATION_STRENGTH,
    V_M_ANCHOR_NUDGE_ENABLED,
    V_M_ANCHOR_TARGET,
)

_V_UPGRADE = {
    "Pause M4": "Master S4",
    "Pause M6": "Pause M6s",
    "Pause M6s": "Master V5",
    "Pause S4": "Master S4",
}


def migration_strength_applies(seed: str | None) -> bool:
    """Deterministic gate — MIGRATION_STRENGTH < 1.0 skips a fraction of migration moves."""
    strength = float(MIGRATION_STRENGTH)
    if strength >= 1.0:
        return True
    if strength <= 0.0:
        return False
    key = (seed or "default").strip()
    bucket = int(hashlib.md5(key.encode()).hexdigest(), 16) % 1000
    return bucket < int(strength * 1000)


def anchor_nudge_probability(seed: str | None) -> float:
    """Per-customer probability of V-line bump when pain profile sits on M-line."""
    if not V_M_ANCHOR_NUDGE_ENABLED:
        return 0.0
    target_v, _target_m = V_M_ANCHOR_TARGET
    # Current full-pipeline V share ~59%; anchor 65% → ~6pp gap → modest nudge rate
    gap = max(0.0, target_v - 0.59)
    key = (seed or "default").strip()
    bucket = int(hashlib.md5(f"anchor:{key}".encode()).hexdigest(), 16) % 1000
    threshold = int(min(0.35, gap * 2.5) * 1000)
    return 1.0 if bucket < threshold else 0.0


def apply_v_m_anchor_nudge(product: str, inputs, ladder: list[str]) -> str:
    """Soft pain-profile nudge from M-line toward accessible V-line when anchor gap remains."""
    if not V_M_ANCHOR_NUDGE_ENABLED:
        return product
    if not segment_axis_is_pain(inputs.ceragem_segment) and inputs.pain_index_category not in {"High", "Medium"}:
        return product
    if product not in _M_LINE_SKUS:
        return product
    if anchor_nudge_probability(inputs.customer_id) <= 0:
        return product

    target = _V_UPGRADE.get(product, "Master S4")
    if target not in ladder and target not in _V_LINE_SKUS:
        return product
    if target.startswith("Master V") or target == "Master S4":
        sku = "Master V5" if target == "Master V5" else target
        if not is_post_promo_v_accessible(
            sku if sku != "Master S4" else "Master V5",
            purchase_power_category=inputs.purchase_power_category,
            zip_income_tier=inputs.zip_income_tier,
        ):
            if target != "Master S4":
                return product
    if target in ladder or target in _V_LINE_SKUS:
        return target
    return product
