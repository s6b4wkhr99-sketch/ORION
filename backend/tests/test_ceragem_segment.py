"""Ceragem Segment tier + axis tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.intelligence.ceragem_rules import (
    ceragem_segment_sort_key,
    compose_ceragem_segment,
    parse_ceragem_axis,
    parse_ceragem_tier,
    resolve_ceragem_tier,
    resolve_segment_axis,
    segment_axis_is_pain,
)
from app.intelligence.types import IntelligenceContext


def test_compose_and_parse_roundtrip():
    segment = compose_ceragem_segment("High+", "Wellness")
    assert segment == "High+ · Wellness"
    assert parse_ceragem_tier(segment) == "High+"
    assert parse_ceragem_axis(segment) == "Wellness"
    assert not segment_axis_is_pain(segment)


def test_legacy_segment_parsing():
    assert parse_ceragem_tier("Mid-Low + Pain Index") == "Mid-Low+"
    assert parse_ceragem_axis("Mid-Low + Pain Index") == "Pain Index"
    assert not segment_axis_is_pain("Mid-High + Wellness")


def test_high_tier_from_premium_zip_and_pp():
    ctx = IntelligenceContext(
        purchase_power_index=0.72,
        pain_index=0.4,
        lifestyle_index=0.55,
        prizm_proxy_segment="Established Elite",
    )
    ctx.zip_intelligence = {
        "premium_zip_indicator": True,
        "income_tier": "High",
        "purchase_potential_score": 0.85,
        "geographic_purchasing_context": 1.0,
    }
    tier = resolve_ceragem_tier(ctx)
    assert tier == "High+", f"expected High+, got {tier}"


def test_mid_high_tier_from_medium_pp_and_zip():
    ctx = IntelligenceContext(
        purchase_power_index=0.55,
        purchase_power_category="Medium",
        pain_index=0.45,
        lifestyle_index=0.5,
    )
    ctx.zip_intelligence = {
        "premium_zip_indicator": False,
        "income_tier": "Mid",
        "purchase_potential_score": 0.55,
        "geographic_purchasing_context": 0.4,
    }
    tier = resolve_ceragem_tier(ctx)
    assert tier == "Mid-High+", f"expected Mid-High+, got {tier}"


def test_five_tier_distribution():
    tiers = set()
    scenarios = [
        (0.82, "High", {"purchase_potential_score": 0.9, "geographic_purchasing_context": 0.5, "premium_zip_indicator": True, "income_tier": "High"}),
        (0.55, "Medium", {"purchase_potential_score": 0.55, "geographic_purchasing_context": 0.4, "premium_zip_indicator": False, "income_tier": "Mid"}),
        (0.55, "Medium", {"purchase_potential_score": 0.45, "geographic_purchasing_context": 0.2, "premium_zip_indicator": False, "income_tier": "Lower"}),
        (0.25, "Low", {"purchase_potential_score": 0.3, "geographic_purchasing_context": 0.2, "premium_zip_indicator": False, "income_tier": "Lower"}),
        (0.25, "Low", {"purchase_potential_score": 0.15, "geographic_purchasing_context": 0.1, "premium_zip_indicator": False, "income_tier": "Lower"}),
    ]
    for pp, pp_cat, zip_intel in scenarios:
        ctx = IntelligenceContext(purchase_power_index=pp, purchase_power_category=pp_cat, pain_index=0.5, lifestyle_index=0.4)
        ctx.zip_intelligence = zip_intel
        tiers.add(resolve_ceragem_tier(ctx))
    assert "High+" in tiers
    assert "Mid-High+" in tiers
    assert "Low+" in tiers
    assert len(tiers) >= 4


def test_axis_pain_from_prizm():
    ctx = IntelligenceContext(
        purchase_power_index=0.5,
        pain_index=0.55,
        lifestyle_index=0.3,
        prizm_proxy_segment="Aging in Place",
    )
    assert resolve_segment_axis(ctx) == "Pain Index"


def test_ceragem_segment_sort_key_tier_then_axis():
    segments = [
        "Mid+ · Wellness",
        "Mid-High+ · Wellness",
        "Mid-High+ · Pain Index",
        "Low+ · Pain Index",
        "High+ · Wellness",
        "Mid-Low + Pain Index",
    ]
    ordered = sorted(segments, key=ceragem_segment_sort_key)
    assert ordered == [
        "High+ · Wellness",
        "Mid-High+ · Pain Index",
        "Mid-High+ · Wellness",
        "Mid+ · Wellness",
        "Mid-Low + Pain Index",
        "Low+ · Pain Index",
    ]


if __name__ == "__main__":
    test_compose_and_parse_roundtrip()
    test_legacy_segment_parsing()
    test_high_tier_from_premium_zip_and_pp()
    test_mid_high_tier_from_medium_pp_and_zip()
    test_five_tier_distribution()
    test_axis_pain_from_prizm()
    test_ceragem_segment_sort_key_tier_then_axis()
    print("ok")
