"""Recommendation rationale tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.intelligence.recommendation_rationale import build_recommendation_rationale
from app.intelligence.recommendation_rules import build_recommendation_inputs, evaluate_recommendation
from app.intelligence.types import IntelligenceContext


def _ctx(**kwargs) -> IntelligenceContext:
    defaults = {
        "customer": {"state": "TX", "zip": "77001", "city": "Houston"},
        "prizm_proxy_segment": "Simple Life",
        "ceragem_segment": "Mid-Low + Pain Index",
        "message_direction": "Pain Relief + Value Message",
        "purchase_power_index": 0.32,
        "purchase_power_category": "Low",
        "pain_index": 0.82,
        "pain_index_category": "High",
        "lifestyle_index": 0.28,
        "lifestyle_category": "Low",
        "email_response_index": 0.41,
        "brand_familiarity_index": 0.55,
        "zip_intelligence": {
            "income_tier": "Lower",
            "sleep_segment": "metro_sleep_deprived",
            "sleep_geo_boost": 0.28,
            "digital_metro_tier": "tier1",
            "brand_geo_boost": 0.42,
        },
    }
    defaults.update(kwargs)
    return IntelligenceContext(**defaults)


def test_rationale_includes_all_six_factors():
    ctx = _ctx()
    inputs = build_recommendation_inputs(ctx)
    result = evaluate_recommendation(inputs)
    ctx.recommended_product = result["product"]["recommended_product"]
    ctx.campaign_strategy = result["strategy"]["campaign_strategy"]
    rationale = build_recommendation_rationale(ctx, result)

    keys = {f["key"] for f in rationale["factors"]}
    assert keys == {
        "purchase_power",
        "pain_index",
        "lifestyle",
        "digital_engagement",
        "brand_familiarity",
        "sleep_affinity",
    }
    assert rationale["recommended_product"]
    assert rationale["selection_rule"]
    assert "추천 제품" in rationale["summary"]


def test_rationale_captures_sleep_adjustment():
    ctx = _ctx()
    inputs = build_recommendation_inputs(ctx)
    result = evaluate_recommendation(inputs)
    ctx.recommended_product = result["product"]["recommended_product"]
    rationale = build_recommendation_rationale(ctx, result)

    sleep_factor = next(f for f in rationale["factors"] if f["key"] == "sleep_affinity")
    assert sleep_factor["level"] == "High"
    assert "수면" in sleep_factor["detail"]
