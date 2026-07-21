"""Tunable promotion policy — Track A (primary SKU) vs Track B (forecast uplift)."""

from __future__ import annotations

PROMO_POLICY_VERSION = "2026.07-promo-policy-v2"

# Track A — Rule-065 primary / migration / convert matrix
PROMO_PRIMARY_SKU_ENABLED = True
PROMO_CONVERT_MATRIX_ENABLED = True
SKU_ALIAS_ENABLED = True

# Track B — orders / revenue forecast without changing recommended_product
PROMO_FORECAST_UPLIFT_ENABLED = True
PROMO_CONVERSION_ELASTICITY = 0.50
PROMO_MAX_UPLIFTED_MULTIPLIER = 2.2

PROMO_SKU_CONVERSION_FLOOR: dict[str, float] = {
    "Master V6": 1.12,
    "Master V5": 1.10,
    "Master S4": 1.18,
    "Pause M10": 1.15,
    "Pause M6s": 1.08,
}

# Post-promo price accessibility tiers (purchase-power score 0–100)
PP_ACCESSIBILITY_LOW_MAX_PRICE = 4200
PP_ACCESSIBILITY_MID_LOW_MAX_PRICE = 5500
PP_ACCESSIBILITY_MID_MAX_PRICE = 6500
PP_ACCESSIBILITY_MID_HIGH_MIN_PRICE = 4200
PP_ACCESSIBILITY_MID_HIGH_MAX_PRICE = 7000
PP_ACCESSIBILITY_HIGH_MIN_PRICE = 7500
PP_ACCESSIBILITY_AFFLUENT_MIN_PRICE = 9000

# V-line post-promo accessibility (legacy boolean gate — prefer promo_price_response module)
V_POST_PROMO_LOW_PP_MAX_PRICE = 4200
V_POST_PROMO_MID_PP_MAX_PRICE = 6500

# Single V-line value entry SKU (Pause S4 legacy name → Master S4 via registry alias)
V_VALUE_ENTRY_SKU = "Master S4"

# Migration tone-down + sales-mix anchor (Recommendation B)
MIGRATION_STRENGTH = 0.75
V_M_ANCHOR_TARGET: tuple[float, float] = (0.65, 0.35)
V_M_ANCHOR_NUDGE_ENABLED = True
WELLNESS_V_WEIGHT = 0.15
