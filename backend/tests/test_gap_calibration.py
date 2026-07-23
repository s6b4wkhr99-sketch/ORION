"""Tests for GAP calibration rule adjustments."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.intelligence.gap_calibration import apply_gap_calibration_adjustments
from app.intelligence.recommendation_rules import RecommendationInputs


def _inputs(**kwargs) -> RecommendationInputs:
    defaults = {
        "ceragem_segment": "Mid-Low+ · Wellness",
        "prizm_segment": "Simple Life",
        "purchase_power_category": "Medium",
        "pain_index_category": "Low",
        "lifestyle_category": "Low",
        "message_direction": "Product Education Message",
        "email_response_index": 0.0,
        "premium_zip": False,
        "zip_income_tier": "Mid",
    }
    defaults.update(kwargs)
    return RecommendationInputs(**defaults)


def test_v9_capped_when_not_high_end():
    ladder = ["Master V9", "Master V7", "Master V6", "Master S4"]
    product, reason = apply_gap_calibration_adjustments("Master V9", _inputs(), ladder)
    assert product != "Master V9"
    assert reason == "gap_v9_cap_not_high_end"


def test_m4_gated_to_s4_for_value_wellness():
    ladder = ["Master S4", "Pause M6s", "Pause M4"]
    product, reason = apply_gap_calibration_adjustments(
        "Pause M4",
        _inputs(
            prizm_segment="Suburban Sophisticates",
            purchase_power_category="Medium",
            zip_income_tier="High",
        ),
        ladder,
    )
    assert product == "Master S4"
    assert reason == "gap_m4_gate_to_s4"


def test_s4_default_for_value_wellness_m6():
    ladder = ["Master S4", "Pause M6s", "Pause M6", "Pause M4"]
    product, reason = apply_gap_calibration_adjustments(
        "Pause M6",
        _inputs(prizm_segment="Unknown", purchase_power_category="Low"),
        ladder,
    )
    assert product == "Master S4"
    assert reason == "gap_s4_default_value_wellness"
