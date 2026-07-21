#!/usr/bin/env python3
"""Tests for baseline vs promo uplift forecast layers."""

from __future__ import annotations

import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from app.intelligence.forecasting import forecast_customer
from app.intelligence.promo_forecast import apply_promo_layers


def test_baseline_conversion_lower_than_uplifted_for_standing_promo():
    result = forecast_customer(
        ceragem_segment="High+ · Wellness",
        recommended_product="Master V9",
        purchase_power_category="Medium",
        purchase_power_index=0.62,
        pain_index=0.42,
        email_response_index=0.5,
        brand_familiarity_index=0.45,
    )
    assert result["baseline_conversion"] > 0
    assert result["conversion_rate"] >= result["baseline_conversion"]
    assert result["promo_uplift"] >= 0
    assert result["expected_revenue"] >= result["baseline_revenue"]


def test_apply_promo_layers_exposes_outreach_sku():
    layers = apply_promo_layers(
        baseline_conversion=0.004,
        intelligence_product="Master V9",
        purchase_power_category="Medium",
        ceragem_segment="High+ · Wellness",
        purchase_power_index=0.6,
        product_price=8999.0,
    )
    assert layers["promo_outreach_product"] == "Master V6"
    assert layers["conversion_rate"] >= layers["baseline_conversion"]


if __name__ == "__main__":
    test_baseline_conversion_lower_than_uplifted_for_standing_promo()
    test_apply_promo_layers_exposes_outreach_sku()
    print("promo_forecast tests passed")
