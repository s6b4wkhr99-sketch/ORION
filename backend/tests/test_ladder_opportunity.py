"""Ladder-addressable product opportunity tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.intelligence.ladder_opportunity import merge_primary_and_ladder_opportunity


def test_all_active_products_appear_on_some_ladder():
    from app.intelligence.product_ladders import CERAGEM_PRODUCT_LADDERS, PRIZM_PRODUCT_LADDERS

    seen: set[str] = set()
    for ladder in CERAGEM_PRODUCT_LADDERS.values():
        seen.update(ladder)
    for ladder in PRIZM_PRODUCT_LADDERS.values():
        seen.update(ladder)
    for product in (
        "Master V9",
        "Master V7",
        "Master V6",
        "Master V5",
        "Master S4",
        "Pause M10",
        "Pause M6",
        "Pause M6s",
        "Pause M4",
    ):
        assert product in seen, product


def test_merge_zip_product_scores_uses_ladder_floor():
    from app.intelligence.ladder_opportunity import merge_zip_product_scores

    primary = {"33101": {"Master V9": {"expected_revenue": 100.0, "target_customers": 5}}}
    ladder = {("33101", "Pause M10"): {"customers": 40, "revenue": 800.0, "orders": 1.0}}
    merged = merge_zip_product_scores(primary, ladder)
    assert merged["33101"]["Pause M10"]["target_customers"] == 40
    assert merged["33101"]["Pause M10"]["expected_revenue"] == 800.0


def test_merge_uses_ladder_floor_when_primary_zero():
    primary = [{"product": "Pause M10", "expected_customers": 0, "expected_orders": 0, "expected_revenue": 0}]
    ladder = {"Pause M10": {"customers": 1200, "orders": 30.0, "revenue": 50000.0}}
    merged = merge_primary_and_ladder_opportunity(primary, ladder)
    row = next(r for r in merged if r["product"] == "Pause M10")
    assert row["expected_customers"] == 1200
    assert row["expected_revenue"] == 50000.0


def test_basic_ladder_pick_respects_income_not_equal_split():
    from app.intelligence.ladder_opportunity import _resolve_promo_aware_ladder_product

    premium = _resolve_promo_aware_ladder_product(
        ceragem="High+ · Wellness",
        prizm="Established Elite",
        pain_cat="Low",
        pp_cat="High",
        ls_cat="High",
        premium_zip=True,
        zip_income_tier="High",
        customer_state="CA",
    )
    value = _resolve_promo_aware_ladder_product(
        ceragem="Low+ · Wellness",
        prizm="Simple Life",
        pain_cat="Low",
        pp_cat="Low",
        ls_cat="Low",
        premium_zip=False,
        zip_income_tier="Lower",
        customer_state="FL",
    )
    assert premium in {"Master V9", "Pause M10"}
    assert value in {"Pause S4", "Pause M4", "Pause M6s", "Master S4"}
    assert premium != value
