"""Tests for SKU migration rules (2026.07-sku-migration-v1)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.intelligence.recommendation_rules import RecommendationInputs, resolve_rule_065_product
from app.intelligence.sku_migration import (
    V_ENTRY_SKU,
    apply_sku_migration,
    normalize_product_code,
    qualifies_m4_to_v5,
    qualifies_v9_to_v7,
    _profile,
)


def _inputs(**kwargs) -> RecommendationInputs:
    defaults = {
        "ceragem_segment": "Mid-Low+ · Pain Index",
        "prizm_segment": "Simple Life",
        "purchase_power_category": "Low",
        "pain_index_category": "High",
        "lifestyle_category": "Low",
        "message_direction": "Pain Relief + Value Message",
        "email_response_index": 0.0,
        "premium_zip": False,
        "zip_income_tier": "Lower",
        "zip_purchase_potential": 0.2,
        "price_resistance_score": 0.0,
        "sleep_geo_boost": 0.0,
        "sleep_deprivation_tier": "none",
        "sleep_segment": "none",
    }
    defaults.update(kwargs)
    return RecommendationInputs(**defaults)


def test_normalize_legacy_v4_to_s4():
    assert normalize_product_code("Master V4") == V_ENTRY_SKU
    assert normalize_product_code("Master S4") == V_ENTRY_SKU


def test_normalize_pause_s4_alias():
    assert normalize_product_code("Pause S4") == V_ENTRY_SKU


def test_pause_s4_pain_routes_to_master_s4():
    inputs = _inputs(
        ceragem_segment="Low+ · Pain Index",
        pain_index_category="Medium",
    )
    result = apply_sku_migration("Pause S4", inputs)
    assert result == V_ENTRY_SKU


def test_pause_m4_pain_routes_to_master_s4():
    inputs = _inputs(
        ceragem_segment="Low+ · Pain Index",
        pain_index_category="Medium",
        lifestyle_category="Low",
        purchase_power_category="Low",
    )
    result = apply_sku_migration("Pause M4", inputs)
    assert result == V_ENTRY_SKU


def test_pause_m4_high_pain_promo_fit_routes_to_v5():
    inputs = _inputs(
        ceragem_segment="Mid+ · Pain Index",
        pain_index_category="High",
        lifestyle_category="High",
        purchase_power_category="Medium",
        zip_income_tier="Mid",
    )
    profile = _profile(inputs)
    assert qualifies_m4_to_v5(profile, promo_ok=True)
    result = apply_sku_migration("Pause M4", inputs)
    assert result == "Master V5"


def test_master_v9_near_premium_routes_to_v7():
    inputs = _inputs(
        ceragem_segment="Mid-High+ · Pain Index",
        pain_index_category="High",
        lifestyle_category="High",
        purchase_power_category="High",
        zip_income_tier="High",
    )
    profile = _profile(inputs)
    assert qualifies_v9_to_v7(profile)
    result = apply_sku_migration("Master V9", inputs)
    assert result == "Master V7"


def test_pause_m6s_high_pain_upsells_to_v7():
    inputs = _inputs(
        ceragem_segment="Mid+ · Pain Index",
        pain_index_category="High",
        lifestyle_category="High",
        purchase_power_category="High",
        zip_income_tier="High",
    )
    result = apply_sku_migration("Pause M6s", inputs)
    assert result == "Master V7"


def test_master_s4_upsells_on_pain_promo():
    inputs = _inputs(
        ceragem_segment="Mid+ · Pain Index",
        pain_index_category="Medium",
        lifestyle_category="Medium",
        purchase_power_category="Medium",
        zip_income_tier="Mid",
    )
    result = apply_sku_migration(V_ENTRY_SKU, inputs)
    assert result in {V_ENTRY_SKU, "Master V6", "Master V5", "Master V7"}


def test_resolve_rule_065_uses_master_s4_not_v4():
    inputs = _inputs(
        ceragem_segment="Low+ · Pain Index",
        pain_index_category="High",
        lifestyle_category="Low",
        purchase_power_category="Low",
        zip_income_tier="Lower",
    )
    result = resolve_rule_065_product(inputs, apply_sleep=False, apply_resistance=False)
    assert result["recommended_product"] != "Master V4"
    assert "Master V4" not in result["product_ladder"]
