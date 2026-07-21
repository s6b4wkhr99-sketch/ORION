"""Recommendation rule tests — ladder-based Rule-065."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.intelligence.product_ladders import (
    CERAGEM_PRODUCT_LADDERS,
    PRIZM_PRODUCT_LADDERS,
    ladder_for_ceragem,
    ladder_for_prizm,
    resolve_active_ladder,
)
from app.intelligence.recommendation_rules import (
    RecommendationInputs,
    adjust_product_for_sleep_deprivation,
    rule_065_product_recommendation,
)


def _inputs(**kwargs) -> RecommendationInputs:
    defaults = {
        "ceragem_segment": "Mid-Low + Pain Index",
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


def test_all_ceragem_segments_have_ladders():
    for key, ladder in CERAGEM_PRODUCT_LADDERS.items():
        assert len(ladder) >= 3, key
        assert ladder_for_ceragem(key) == list(ladder)


def test_all_prizm_segments_have_ladders():
    for key, ladder in PRIZM_PRODUCT_LADDERS.items():
        assert len(ladder) >= 3, key
        assert ladder_for_prizm(key) == list(ladder)


def test_pain_axis_uses_ceragem_ladder_over_prizm():
    ladder, source = resolve_active_ladder(
        ceragem_segment="Mid-Low+ · Pain Index",
        prizm_segment="Simple Life",
        pain_index_category="Medium",
    )
    assert source == "ceragem"
    assert ladder[0] == "Master V5"


def test_wellness_uses_prizm_ladder():
    ladder, source = resolve_active_ladder(
        ceragem_segment="Mid-Low+ · Wellness",
        prizm_segment="Caregiving Households",
        pain_index_category="Low",
    )
    assert source == "prizm"
    assert ladder[0] == "Master S4"


def test_pain_high_lower_zip_uses_ceragem_pain_ladder():
    result = rule_065_product_recommendation(_inputs(lifestyle_category="Medium"))
    # Mid-Low Pain ladder: V5 → V6 → S4 → M4; promo-active pain may upsell to V5
    assert result["recommended_product"] in {"Master S4", "Master V5", "Master V6"}
    assert result["ladder_source"] == "ceragem"


def test_pain_high_lifestyle_low_steps_further():
    result = rule_065_product_recommendation(_inputs(lifestyle_category="Low"))
    # Ladder → Pause M4; SKU migration pain-path → Master S4
    assert result["recommended_product"] == "Master S4"


def test_caregiving_wellness_recommends_master_s4():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Mid-Low + Wellness",
            prizm_segment="Caregiving Households",
            pain_index_category="Low",
            lifestyle_category="Low",
            purchase_power_category="Low",
            zip_income_tier="Mid",
            sleep_geo_boost=0.30,
        )
    )
    assert result["recommended_product"] == "Master S4"
    assert result["ladder_source"] == "prizm"


def test_caregiving_medium_lifestyle_steps_to_m6s_with_promo():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Mid-Low + Wellness",
            prizm_segment="Caregiving Households",
            pain_index_category="Low",
            lifestyle_category="Medium",
            purchase_power_category="Low",
            zip_income_tier="Mid",
            sleep_geo_boost=0.30,
        )
    )
    assert result["recommended_product"] == "Pause M6s"


def test_lower_income_wellness_standard_m4_without_promo_expansion(monkeypatch):
    from app.commercial import promotion_policy

    monkeypatch.setattr(promotion_policy, "is_promotion_active", lambda code: False)
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Low+ · Wellness",
            prizm_segment="Unknown",
            pain_index_category="Low",
            lifestyle_category="Medium",
            purchase_power_category="Low",
            zip_income_tier="Mid",
        )
    )
    assert result["recommended_product"] in {"Pause M4", "Pause M6s"}


def test_m4_expands_to_s4_when_s4_promo_active(monkeypatch):
    from app.commercial import promotion_policy

    monkeypatch.setattr(
        promotion_policy,
        "is_promotion_active",
        lambda code: code == "Master S4",
    )
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Low+ · Wellness",
            prizm_segment="Unknown",
            pain_index_category="Low",
            lifestyle_category="Low",
            purchase_power_category="Low",
            zip_income_tier="Lower",
        )
    )
    assert result["recommended_product"] == "Master S4"


def test_simple_life_value_ladder_preserved_under_sleep():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Low+ · Wellness",
            prizm_segment="Simple Life",
            pain_index_category="Low",
            lifestyle_category="Low",
            purchase_power_category="Low",
            zip_income_tier="Lower",
            sleep_geo_boost=0.30,
        )
    )
    assert result["recommended_product"] == "Master S4"
    assert result["sleep_deprivation_adjustment"]["adjustment_reason"] == "value_massage_preserved"


def test_established_elite_uses_prizm_ladder():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="High+ · Wellness",
            prizm_segment="Established Elite",
            pain_index_category="Low",
            lifestyle_category="High",
            purchase_power_category="High",
            zip_income_tier="High",
        )
    )
    assert result["recommended_product"] == "Master V9"
    assert result["ladder_source"] == "prizm"


def test_established_elite_ca_keeps_master_v9():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="High+ · Wellness",
            prizm_segment="Established Elite",
            pain_index_category="Low",
            lifestyle_category="High",
            purchase_power_category="High",
            zip_income_tier="High",
            customer_state="CA",
        )
    )
    assert result["recommended_product"] == "Master V9"


def test_m10_wellness_nationwide_high_pp():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Mid+ · Wellness",
            prizm_segment="Kids and Cul-de-Sacs",
            pain_index_category="Low",
            lifestyle_category="Medium",
            purchase_power_category="High",
            zip_income_tier="Mid",
            premium_zip=False,
            customer_state="TX",
        )
    )
    assert result["ladder_source"] == "prizm"
    assert result["recommended_product"] == "Pause M10"


def test_s4_expansion_nationwide_when_promo_active():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Low+ · Wellness",
            prizm_segment="Simple Life",
            pain_index_category="Low",
            lifestyle_category="Low",
            purchase_power_category="Low",
            zip_income_tier="Lower",
            customer_state="OH",
        )
    )
    assert result["recommended_product"] == "Master S4"


def test_v6_promo_expansion_on_pain_profile():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Mid-High+ · Pain Index",
            prizm_segment="Wellness Seekers",
            pain_index_category="High",
            lifestyle_category="Medium",
            purchase_power_category="Medium",
            zip_income_tier="Mid",
            premium_zip=False,
        )
    )
    assert result["recommended_product"] == "Master V6"


def test_fl_value_cohort_prefers_pause_s4():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Low+ · Wellness",
            prizm_segment="Simple Life",
            pain_index_category="Low",
            lifestyle_category="Low",
            purchase_power_category="Low",
            zip_income_tier="Lower",
            customer_state="FL",
        )
    )
    assert result["recommended_product"] == "Master S4"


def test_ny_suburban_sophisticates_keeps_master_v9():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="High+ · Wellness",
            prizm_segment="Suburban Sophisticates",
            pain_index_category="Low",
            lifestyle_category="High",
            purchase_power_category="High",
            zip_income_tier="High",
            customer_state="NY",
        )
    )
    assert result["recommended_product"] == "Master V9"


def test_standing_promo_maps_pause_m6_to_m6s_for_value_cohort():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Mid+ · Wellness",
            prizm_segment="Booming with Confidence",
            pain_index_category="Low",
            purchase_power_category="Low",
            lifestyle_category="Low",
            zip_income_tier="Lower",
        )
    )
    assert result["recommended_product"] == "Pause M6s"


def test_pause_m6_stays_when_m6s_promo_inactive(monkeypatch):
    from app.commercial import promotion_policy

    monkeypatch.setattr(promotion_policy, "is_promotion_active", lambda code: False)
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Mid+ · Wellness",
            prizm_segment="Booming with Confidence",
            pain_index_category="Low",
            purchase_power_category="Low",
            lifestyle_category="Low",
            zip_income_tier="Lower",
        )
    )
    assert result["recommended_product"] == "Pause M6"


def test_suburban_sophisticates_ladder():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="High+ · Wellness",
            prizm_segment="Suburban Sophisticates",
            pain_index_category="Low",
            lifestyle_category="High",
            purchase_power_category="High",
            zip_income_tier="High",
        )
    )
    assert result["recommended_product"] == "Master V9"


def test_v9_requires_premium_or_high_income_high_pp_zip():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="High+ · Wellness",
            prizm_segment="Suburban Sophisticates",
            pain_index_category="Low",
            lifestyle_category="High",
            purchase_power_category="High",
            zip_income_tier="Mid",
            premium_zip=False,
        )
    )
    assert result["recommended_product"] == "Master V7"


def test_mid_plus_wellness_defaults_to_m6s_not_m10():
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Mid+ · Wellness",
            prizm_segment="Booming with Confidence",
            pain_index_category="Low",
            lifestyle_category="Medium",
            purchase_power_category="Medium",
            zip_income_tier="Mid",
            premium_zip=False,
        )
    )
    assert result["recommended_product"] != "Pause M10"


def test_v6_capped_without_affluent_zip_when_promo_inactive(monkeypatch):
    from app.commercial import promotion_policy

    monkeypatch.setattr(promotion_policy, "is_promotion_active", lambda code: False)
    result = rule_065_product_recommendation(
        _inputs(
            ceragem_segment="Mid-High+ · Pain Index",
            prizm_segment="Wellness Seekers",
            pain_index_category="High",
            lifestyle_category="Medium",
            purchase_power_category="Medium",
            zip_income_tier="Mid",
            premium_zip=False,
        )
    )
    assert result["recommended_product"] != "Master V6"
    assert result["recommended_product"] in {"Master V5", "Pause M6", "Master S4", "Pause M4"}


def test_sleep_city_preserves_master_v_for_pain_high():
    result = adjust_product_for_sleep_deprivation(
        "Master S4",
        _inputs(
            pain_index_category="High",
            sleep_geo_boost=0.28,
            sleep_deprivation_tier="tier1_sleep_deprived",
        ),
    )
    assert result["adjusted_product"] == "Master S4"
    assert result["adjusted"] is False


def test_sleep_still_preserves_master_s4_on_pain_axis():
    # Master S4 is FDA Class 2 — sleep nudge preserves therapeutic V on pain axis
    result = adjust_product_for_sleep_deprivation(
        "Master S4",
        _inputs(
            ceragem_segment="Mid-Low + Pain Index",
            pain_index_category="Medium",
            sleep_geo_boost=0.28,
            sleep_deprivation_tier="tier1_sleep_deprived",
        ),
    )
    assert result["adjusted_product"] == "Master S4"
    assert result["adjusted"] is False


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("ok")
