"""Tests for buyer GAP SKU mapping (isolated from dashboard KPIs)."""

from app.intelligence.buyer_gap_mapping import (
    M2_COUNTERPART,
    V4_DEFAULT_COUNTERPART,
    V4_UPTIER_COUNTERPART,
    buyer_compare_sku,
    parse_purchase_token,
    v4_prospect_counterpart,
)


def test_m2_maps_to_pause_m4():
    sku, rule = buyer_compare_sku("Ceragem Master M2")
    assert sku == M2_COUNTERPART
    assert rule == "m2_to_m4"


def test_v4_default_is_master_s4():
    sku, rule = v4_prospect_counterpart(
        ceragem_segment="Low+ · Wellness",
        prizm_proxy_segment="Simple Life",
        purchase_power_index=0.3,
        lifestyle_index=0.4,
    )
    assert sku == V4_DEFAULT_COUNTERPART
    assert rule == "default_s4"


def test_v4_splits_to_v5_for_premium_prizm():
    sku, rule = v4_prospect_counterpart(
        ceragem_segment="High+ · Wellness",
        prizm_proxy_segment="Established Elite",
        purchase_power_index=0.55,
        lifestyle_index=0.85,
    )
    assert sku == V4_UPTIER_COUNTERPART
    assert rule == "prizm_premium"


def test_v4_splits_to_v5_for_pain_ladder():
    sku, rule = v4_prospect_counterpart(
        ceragem_segment="Mid-Low+ · Pain Index",
        prizm_proxy_segment="Caregiving Households",
        purchase_power_index=0.25,
        lifestyle_index=0.85,
    )
    assert sku == V4_UPTIER_COUNTERPART
    assert rule == "ceragem_v5_ladder"


def test_v4_splits_to_v5_for_high_purchase_power():
    sku, rule = v4_prospect_counterpart(
        ceragem_segment="Mid-Low+ · Wellness",
        prizm_proxy_segment="Unknown",
        purchase_power_index=0.8,
        lifestyle_index=0.5,
    )
    assert sku == V4_UPTIER_COUNTERPART
    assert rule == "purchase_power_high"


def test_direct_map_for_v6():
    sku, rule = buyer_compare_sku("Ceragem Master V6")
    assert sku == "Master V6"
    assert rule == "direct_map"


def test_m6s_from_shopify_product_title():
    product = "CERAGEM M6 - M6(s) - Only Massage Chair / Beige"
    assert parse_purchase_token(product) == "M6S"
    sku, rule = buyer_compare_sku(product)
    assert sku == "Pause M6s"
    assert rule == "direct_map"


def test_m6_without_s_suffix_stays_m6():
    product = "CERAGEM M6 - M6 - With Accessories / Brown"
    assert parse_purchase_token(product) == "M6"
    sku, rule = buyer_compare_sku(product)
    assert sku == "Pause M6"
    assert rule == "direct_map"


def test_m6s_token_literal():
    assert parse_purchase_token("Ceragem Pause M6S Chair") == "M6S"
