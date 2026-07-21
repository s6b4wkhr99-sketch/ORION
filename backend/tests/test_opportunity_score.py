#!/usr/bin/env python3
"""Tests for state opportunity score computation."""

from __future__ import annotations

import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from app.campaign.opportunity_score import (
    _price_accessibility_fit,
    _series_fit_bonus,
    apply_radar_axis_spreads,
    compute_state_opportunity_score,
    compute_zip_opportunity_score,
)
from app.commercial.engine import effective_customer_payment


def test_high_pain_v_series_scores_higher_than_low_pain():
    base = {
        "revenue": 500_000,
        "conversion": 0.003,
        "lifestyle_score": 55,
        "purchase_power_score": 60,
        "brand_score": 50,
        "digital_score": 45,
    }
    low_pain = {**base, "pain_index_score": 25, "top_product": "Pause S4"}
    high_pain_v = {**base, "pain_index_score": 72, "top_product": "Master V7"}
    low_score = compute_state_opportunity_score(low_pain, max_revenue=2_000_000)
    high_score = compute_state_opportunity_score(high_pain_v, max_revenue=2_000_000)
    assert high_score > low_score
    assert high_score - low_score >= 8


def test_series_fit_bonus_balanced_across_series():
    v_bonus = _series_fit_bonus("Master V7", pain_score=60, lifestyle_score=30)
    m_bonus = _series_fit_bonus("Pause M4", pain_score=30, lifestyle_score=55)
    s_bonus = _series_fit_bonus("Master S4", pain_score=32, lifestyle_score=45)
    assert 0 < v_bonus <= 10
    assert 0 < m_bonus <= 10
    assert 0 < s_bonus <= 10
    assert max(v_bonus, m_bonus, s_bonus) - min(v_bonus, m_bonus, s_bonus) <= 4


def test_zip_score_uses_intelligence_product_not_outreach_mapping():
    base = {
        "revenue": 400_000,
        "conversion": 0.004,
        "purchase_power": "Medium",
        "purchase_power_index_score": 58,
        "campaign_priority_index_score": 55,
        "pain_index_score": 52,
        "lifestyle_index_score": 48,
        "brand_index_score": 50,
        "ceragem_segment": "Mid+ · Wellness",
    }
    m_intel = {
        **base,
        "recommended_product": "Pause M4",
        "intelligence_product": "Pause M4",
        "top_product": "Pause S4",
    }
    v_intel = {
        **base,
        "recommended_product": "Master V9",
        "intelligence_product": "Master V9",
        "top_product": "Master V6",
    }
    m_score = compute_zip_opportunity_score(m_intel, max_revenue=2_000_000)
    v_score = compute_zip_opportunity_score(v_intel, max_revenue=2_000_000)
    assert m_score > 0
    assert abs(m_score - v_score) < 12


def test_series_fit_bonus_differentiates_products():
    v_bonus = _series_fit_bonus("Master V7", pain_score=60, lifestyle_score=30)
    m_bonus = _series_fit_bonus("Pause M4", pain_score=30, lifestyle_score=55)
    assert v_bonus > 0
    assert m_bonus > 0


def test_opportunity_score_within_bounds():
    row = {
        "revenue": 2_000_000,
        "conversion": 0.006,
        "pain_index_score": 80,
        "purchase_power_score": 85,
        "lifestyle_score": 70,
        "brand_score": 75,
        "digital_score": 68,
        "top_product": "Master V9",
    }
    score = compute_state_opportunity_score(row, max_revenue=2_000_000)
    assert 8 <= score <= 99


def test_spread_widens_pain_axis_oh_vs_al():
    rows = [
        {"state": "OH", "pain_index_score": 50.0, "lifestyle_score": 30.0, "brand_score": 35.0},
        {"state": "AL", "pain_index_score": 29.0, "lifestyle_score": 42.0, "brand_score": 32.0},
        {"state": "MN", "pain_index_score": 28.0, "lifestyle_score": 38.0, "brand_score": 30.0},
    ]
    spread = apply_radar_axis_spreads(rows)
    by_state = {r["state"]: r for r in spread}
    assert by_state["OH"]["pain_index_score"] > by_state["AL"]["pain_index_score"] + 40
    assert by_state["AL"]["lifestyle_score"] > by_state["OH"]["lifestyle_score"] + 40


def test_spread_includes_purchase_power_and_lifestyle():
    rows = [
        {"state": "VA", "pain_index_score": 28.0, "lifestyle_score": 48.0, "purchase_power_score": 72.0, "brand_score": 40.0, "digital_score": 45.0},
        {"state": "AL", "pain_index_score": 29.0, "lifestyle_score": 55.0, "purchase_power_score": 38.0, "brand_score": 32.0, "digital_score": 30.0},
        {"state": "OH", "pain_index_score": 50.0, "lifestyle_score": 30.0, "purchase_power_score": 42.0, "brand_score": 35.0, "digital_score": 32.0},
    ]
    spread = apply_radar_axis_spreads(rows)
    by_state = {r["state"]: r for r in spread}
    assert by_state["VA"]["purchase_power_score"] > by_state["AL"]["purchase_power_score"] + 25
    assert by_state["AL"]["lifestyle_score"] > by_state["OH"]["lifestyle_score"] + 25


def test_low_purchase_power_favors_accessible_skus():
    base = {
        "revenue": 200_000,
        "conversion": 0.003,
        "pain_index_score": 40,
        "purchase_power_score": 28,
        "lifestyle_score": 42,
        "brand_score": 40,
        "digital_score": 35,
        "lifestyle_tier": "Lower Income Geography",
    }
    value_sku = {**base, "top_product": "Pause M4"}
    premium_sku = {**base, "top_product": "Master V9"}
    value_score = compute_state_opportunity_score(value_sku, max_revenue=2_000_000)
    premium_score = compute_state_opportunity_score(premium_sku, max_revenue=2_000_000)
    assert value_score > premium_score


def test_premium_lifestyle_favors_v_series_over_entry_skus():
    base = {
        "revenue": 300_000,
        "conversion": 0.003,
        "pain_index_score": 35,
        "purchase_power_score": 72,
        "lifestyle_score": 68,
        "brand_score": 55,
        "digital_score": 50,
        "lifestyle_tier": "Premium Wellness Geography",
    }
    v7 = {**base, "top_product": "Master V7"}
    m4 = {**base, "top_product": "Pause M4"}
    assert compute_state_opportunity_score(v7, max_revenue=2_000_000) > compute_state_opportunity_score(
        m4, max_revenue=2_000_000
    )


def test_recommendation_products_include_v_and_m_series_minimum():
    from app.campaign.opportunity_score import recommendation_products_for_purchase_power_band

    products = recommendation_products_for_purchase_power_band(
        52.0,
        ["Master S4", "Pause M4", "Pause M6"],
    )
    v_count = sum(1 for p in products if p.startswith("Master V"))
    m_count = sum(1 for p in products if p.startswith("Pause M") or p == "Pause S4")
    assert v_count >= 2, products
    assert m_count >= 2, products
    assert len(products) <= 6


def test_ceragem_segment_recommendation_products_use_tier_score():
    from app.campaign.opportunity_score import (
        purchase_power_score_from_ceragem_segment,
        recommendation_products_for_ceragem_segment,
    )

    assert purchase_power_score_from_ceragem_segment("High+ · Wellness") == 90.0
    assert purchase_power_score_from_ceragem_segment("Mid-Low + Pain Index") == 45.0
    products = recommendation_products_for_ceragem_segment(
        "Mid+ · Wellness",
        ["Master V6", "Pause M6"],
    )
    v_count = sum(1 for p in products if p.startswith("Master V"))
    m_count = sum(1 for p in products if p.startswith("Pause M") or p == "Pause S4")
    assert v_count >= 2, products
    assert m_count >= 2, products


def test_effective_customer_payment_applies_standing_promos():
    assert effective_customer_payment("Pause M6") == 4999.0
    assert effective_customer_payment("Pause M6s") == 3839.2
    assert effective_customer_payment("Master V6") == 5119.2
    assert effective_customer_payment("Master S4") == 3849.3
    assert effective_customer_payment("Pause M10") == 6859.3


def test_m6_vs_m6s_price_fit_differs_at_low_purchase_power():
    pp = 30.0
    m6 = _price_accessibility_fit("Pause M6", pp)
    m6s = _price_accessibility_fit("Pause M6s", pp)
    assert m6 == 6.0
    assert m6s == 9.0
    assert m6s > m6


def test_pause_m6_radar_uses_m6s_outreach_effective_price():
    base = {
        "revenue": 200_000,
        "conversion": 0.003,
        "pain_index_score": 40,
        "purchase_power_score": 32,
        "lifestyle_score": 55,
        "brand_score": 40,
        "digital_score": 35,
        "lifestyle_tier": "Lower Income Geography",
        "purchase_power_tier": "Lower Income Geography",
        "ceragem_segment": "Mid-Low+ · Wellness",
    }
    m6 = compute_state_opportunity_score({**base, "top_product": "Pause M6"}, max_revenue=2_000_000)
    m6s = compute_state_opportunity_score({**base, "top_product": "Pause M6s"}, max_revenue=2_000_000)
    premium = compute_state_opportunity_score({**base, "top_product": "Master V9"}, max_revenue=2_000_000)
    assert m6 == m6s
    assert m6 > premium


if __name__ == "__main__":
    test_high_pain_v_series_scores_higher_than_low_pain()
    test_series_fit_bonus_balanced_across_series()
    test_zip_score_uses_intelligence_product_not_outreach_mapping()
    test_series_fit_bonus_differentiates_products()
    test_spread_widens_pain_axis_oh_vs_al()
    test_spread_includes_purchase_power_and_lifestyle()
    test_opportunity_score_within_bounds()
    test_low_purchase_power_favors_accessible_skus()
    test_premium_lifestyle_favors_v_series_over_entry_skus()
    test_recommendation_products_include_v_and_m_series_minimum()
    test_ceragem_segment_recommendation_products_use_tier_score()
    test_effective_customer_payment_applies_standing_promos()
    test_m6_vs_m6s_price_fit_differs_at_low_purchase_power()
    test_pause_m6_radar_uses_m6s_outreach_effective_price()
    print("opportunity_score tests passed")
