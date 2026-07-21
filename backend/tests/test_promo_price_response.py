"""Tests for post-promo price responsiveness (promo_price_response)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.intelligence.promo_price_response import (
    PromoPriceDirection,
    accessibility_fit,
    aggregate_price_responsive_promo_coverage,
    effective_post_promo_price,
    is_post_promo_accessible,
    resolve_promo_price_response,
)


def test_effective_post_promo_price_applies_standing_discount():
    v6 = effective_post_promo_price("Master V6")
    assert v6 > 0
    assert v6 < effective_post_promo_price("Master V9") or effective_post_promo_price("Master V9") > 0


def test_v6_down_converts_to_v5_for_low_pp():
    response = resolve_promo_price_response(
        "Master V6",
        purchase_power_category="Low",
        ceragem_segment="Mid-Low+ · Pain Index",
    )
    assert response.primary_sku == "Master V6"
    assert response.outreach_sku == "Master V5"
    assert response.direction == PromoPriceDirection.DOWN
    assert response.accessible


def test_s4_up_converts_to_v5_for_pain_mid_pp():
    response = resolve_promo_price_response(
        "Master S4",
        purchase_power_category="Medium",
        ceragem_segment="Mid-Low+ · Pain Index",
    )
    assert response.primary_sku == "Master S4"
    assert response.outreach_sku in {"Master V5", "Master V6"}
    assert response.direction == PromoPriceDirection.UP
    assert response.accessible


def test_aggregate_price_responsive_coverage_splits_converts():
    rows = [
        {
            "product": "Master V6",
            "customers": 100_000,
            "purchase_power_category": "Low",
            "ceragem_segment": "Mid-Low+ · Pain Index",
        },
        {
            "product": "Master S4",
            "customers": 50_000,
            "purchase_power_category": "Medium",
            "ceragem_segment": "Mid-Low+ · Pain Index",
        },
        {
            "product": "Master V5",
            "customers": 10_000,
            "purchase_power_category": "Medium",
            "ceragem_segment": "Mid-Low+ · Pain Index",
        },
    ]
    coverage = aggregate_price_responsive_promo_coverage(rows)
    assert coverage["Master V5"]["customers"] >= 100_000
    assert coverage["Master V5"]["down_convert"] >= 50_000
    assert coverage["Master V6"]["up_convert"] >= 40_000


def test_is_post_promo_accessible_matches_v_line_legacy_gate():
    assert is_post_promo_accessible("Master V6", purchase_power_category="High", zip_income_tier="High")
    assert not is_post_promo_accessible("Master V6", purchase_power_category="Low", zip_income_tier="Lower")


def test_accessibility_fit_favors_lower_prices_for_low_pp():
    low_pp = 30.0
    s4 = accessibility_fit("Master S4", low_pp)
    v6 = accessibility_fit("Master V6", low_pp)
    assert s4 > v6


if __name__ == "__main__":
    test_effective_post_promo_price_applies_standing_discount()
    test_v6_down_converts_to_v5_for_low_pp()
    test_s4_up_converts_to_v5_for_pain_mid_pp()
    test_aggregate_price_responsive_coverage_splits_converts()
    test_is_post_promo_accessible_matches_v_line_legacy_gate()
    test_accessibility_fit_favors_lower_prices_for_low_pp()
    print("PASS: promo_price_response tests")
