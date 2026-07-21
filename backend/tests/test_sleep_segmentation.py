"""Sleep segmentation tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.intelligence.sleep_segmentation import compute_sleep_affinity
from app.intelligence.types import IntelligenceContext


def _ctx(**kwargs) -> IntelligenceContext:
    ctx = IntelligenceContext(customer={"state": "PA", "city": "Philadelphia", "zip": "19107"})
    defaults = {
        "prizm_proxy_segment": "Simple Life",
        "ceragem_segment": "Mid-Low + Pain Index",
        "pain_index_category": "Medium",
        "lifestyle_category": "Low",
        "purchase_power_category": "Low",
        "zip_intelligence": {
            "sleep_city_boost": 0.28,
            "income_tier": "Lower",
        },
    }
    for key, value in {**defaults, **kwargs}.items():
        setattr(ctx, key, value)
    return ctx


def test_metro_plus_simple_life_sleep_affinity():
    result = compute_sleep_affinity(_ctx())
    assert result["sleep_geo_boost"] >= 0.35
    assert result["sleep_segment"] == "metro_plus_prizm_sleep_affinity"
    assert result["sleep_deprivation_match"] is True


def test_simple_life_only_sleep_segment():
    result = compute_sleep_affinity(
        _ctx(
            zip_intelligence={"sleep_city_boost": 0.0, "income_tier": "Mid"},
            ceragem_segment="Mid-High + Wellness",
            pain_index_category="Low",
            purchase_power_category="Medium",
            lifestyle_category="Medium",
        )
    )
    assert result["sleep_geo_boost"] == 0.18
    assert result["sleep_segment"] == "simple_life_sleep_stress"


def test_pain_high_without_metro_skips_sleep_boost():
    result = compute_sleep_affinity(
        _ctx(
            pain_index_category="High",
            zip_intelligence={"sleep_city_boost": 0.0, "income_tier": "Lower"},
        )
    )
    assert result["sleep_geo_boost"] == 0.0


def test_metro_tier1_preserved_for_pain_high():
    result = compute_sleep_affinity(
        _ctx(
            pain_index_category="High",
            zip_intelligence={"sleep_city_boost": 0.28, "income_tier": "Lower"},
        )
    )
    assert result["sleep_geo_boost"] >= 0.28


if __name__ == "__main__":
    test_metro_plus_simple_life_sleep_affinity()
    test_simple_life_only_sleep_segment()
    test_pain_high_without_metro_skips_sleep_boost()
    test_metro_tier1_preserved_for_pain_high()
    print("ok")
