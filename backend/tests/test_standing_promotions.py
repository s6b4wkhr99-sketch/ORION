"""Standing promotion catalog and Mission Control commercial summary."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.campaign.opportunity_score import _promotion_accessibility_fit
from app.commercial.engine import build_commercial_kpis, default_promotion_amount, effective_customer_payment
from app.commercial.summary import build_commercial_intelligence_summary
from app.reference.registry import ACTIVE_STANDING_PROMOTION_ORDER, ACTIVE_STANDING_PROMOTIONS, PRODUCT_CATALOG


def _mock_db() -> MagicMock:
    db = MagicMock()
    db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 0
    return db


def test_standing_promotion_catalog_matches_operating_plan():
    assert tuple(ACTIVE_STANDING_PROMOTIONS) == ACTIVE_STANDING_PROMOTION_ORDER
    assert ACTIVE_STANDING_PROMOTIONS["Master V6"]["default_promotion_pct"] == 0.20
    assert ACTIVE_STANDING_PROMOTIONS["Master V5"]["default_promotion_pct"] == 0.20
    assert ACTIVE_STANDING_PROMOTIONS["Master S4"]["default_promotion_pct"] == 0.30
    assert ACTIVE_STANDING_PROMOTIONS["Pause M10"]["default_promotion_pct"] == 0.30
    assert ACTIVE_STANDING_PROMOTIONS["Pause M6s"]["default_promotion_pct"] == 0.20

    inactive_promo_codes = {
        p["code"]: p.get("promo_code")
        for p in PRODUCT_CATALOG
        if p.get("active", True) and p["code"] not in ACTIVE_STANDING_PROMOTIONS
    }
    assert inactive_promo_codes == {
        "Master V9": None,
        "Master V7": None,
        "Pause M6": None,
        "Pause M4": None,
    }


def test_net_margin_matches_commercial_sheet():
    v9 = build_commercial_kpis("Master V9", default_promotion_amount("Master V9"))
    v6 = build_commercial_kpis("Master V6", default_promotion_amount("Master V6"))
    assert round(v9["net_profit_pct"] * 100, 2) == 45.19
    assert round(v6["net_profit_pct"] * 100, 2) == 45.21
    assert v6["net_profit_pct"] > 0.45


def test_default_promotion_amount_only_for_standing_skus():
    assert default_promotion_amount("Master V6") == 1600.0
    assert default_promotion_amount("Pause M6s") == 1200.0
    assert default_promotion_amount("Master V7") == 1500.0
    assert default_promotion_amount("Master S4") == 0.0
    assert effective_customer_payment("Master S4") == 3849.3
    assert effective_customer_payment("Master V6") == 5119.2
    assert effective_customer_payment("Pause M6s") == 3839.2


def test_promotion_fit_only_for_standing_skus():
    from app.commercial.promotion_policy import active_promotion_order

    low_pp = 30.0
    assert _promotion_accessibility_fit("Master V6", low_pp) > 0
    assert _promotion_accessibility_fit("Pause M6s", low_pp) > 0
    assert _promotion_accessibility_fit("Master V7", low_pp) == 0
    assert _promotion_accessibility_fit("Pause M6", low_pp) == 0
    assert len(active_promotion_order()) >= 5


def test_commercial_summary_active_promotions_list():
    summary = build_commercial_intelligence_summary(
        db=_mock_db(),
        upload_id=None,
        product_rows=[],
        expected_revenue=0.0,
        expected_orders=0.0,
        le_frame_incentive=0.0,
    )
    promos = summary["active_promotions"]
    assert [row["product"] for row in promos] == list(ACTIVE_STANDING_PROMOTION_ORDER)
    assert {row["product"]: row["default_promotion_pct"] for row in promos} == {
        "Master V6": 20.0,
        "Master V5": 20.0,
        "Master S4": 30.0,
        "Pause M10": 30.0,
        "Pause M6s": 20.0,
    }
    assert summary["kpi_basis"] == "standing_promotion_policy"
    assert summary["best_standing_promo_sku"]["product"] == "Master V6"
    assert summary["best_standing_promo_sku"]["standing_promotion"] is True
    assert summary["best_standing_promo_sku"]["standing_promotion_margin_pct"] == 0.20
    assert round(summary["best_standing_promo_sku"]["net_profit_pct"] * 100, 2) == 45.21
    assert summary["highest_margin_sku"]["product"] == "Master V9"
    assert round(summary["highest_margin_sku"]["net_profit_pct"] * 100, 2) == 45.19
    assert summary["highest_margin_sku"]["standing_promotion"] is False
    assert summary["commercial_health_score"] > 50


def test_catalog_consolidates_pause_s4_into_master_s4():
    from app.commercial.catalog import consolidate_catalog_skus

    catalog = [
        {
            "code": "Master S4",
            "name": "Master S4",
            "active": True,
            "promo_code": None,
            "default_promotion_pct": None,
            "max_promotion": 0,
        },
        {
            "code": "Pause S4",
            "name": "Pause S4",
            "active": True,
            "promo_code": "SAVE30",
            "default_promotion_pct": 0.30,
            "max_promotion": 1800,
        },
    ]
    merged = consolidate_catalog_skus(catalog)
    by_code = {row["code"]: row for row in merged}
    assert "Pause S4" not in by_code
    assert by_code["Master S4"]["promo_code"] == "SAVE30"
    assert by_code["Master S4"]["default_promotion_pct"] == 0.30


def test_catalog_policy_preserves_runtime_promo_fields():
    from app.commercial.catalog import normalize_catalog_promotions

    catalog = [
        {
            "code": "Master V7",
            "active": True,
            "promo_code": "SAVE20",
            "default_promotion_pct": 0.18,
        },
        {
            "code": "Pause M6",
            "active": True,
            "promo_code": "SAVE20",
            "default_promotion_pct": 0.23,
        },
        {
            "code": "Master V6",
            "active": True,
            "promo_code": "SPRING25",
            "default_promotion_pct": 0.25,
        },
        {
            "code": "Master V9",
            "active": True,
            "promo_code": None,
            "default_promotion_pct": 0.10,
        },
    ]
    patched = normalize_catalog_promotions(catalog)
    by_code = {row["code"]: row for row in patched}
    assert by_code["Master V7"]["promo_code"] == "SAVE20"
    assert by_code["Pause M6"]["promo_code"] == "SAVE20"
    assert by_code["Master V6"]["promo_code"] == "SPRING25"
    assert by_code["Master V6"]["default_promotion_pct"] == 0.25
    assert by_code["Master V9"]["promo_code"] is None
    assert by_code["Master V9"]["default_promotion_pct"] is None


def test_promotion_coverage_is_per_standing_sku_not_merged_promo_code():
    product_rows = [
        {"product": "Pause M10", "customers": 120_000, "revenue": 10_000_000, "share_pct": 40.0},
        {"product": "Master S4", "customers": 8_000, "revenue": 500_000, "share_pct": 2.0},
        {"product": "Master V6", "customers": 0, "revenue": 0, "share_pct": 0.0},
        {"product": "Master V5", "customers": 15_000, "revenue": 900_000, "share_pct": 5.0},
        {"product": "Pause M6s", "customers": 5_000, "revenue": 300_000, "share_pct": 1.5},
        {"product": "Master V9", "customers": 50_000, "revenue": 5_000_000, "share_pct": 20.0},
    ]
    summary = build_commercial_intelligence_summary(
        db=_mock_db(),
        upload_id=None,
        product_rows=product_rows,
        expected_revenue=0.0,
        expected_orders=0.0,
        le_frame_incentive=0.0,
        targetable_customers=200_000,
    )
    coverage = {row["product"]: row for row in summary["promotion_coverage"] if row.get("product")}
    assert coverage["Pause M10"]["customers"] == 120_000
    assert coverage["Master S4"]["customers"] == 8_000
    assert coverage["Master V6"]["customers"] == 0
    assert coverage["Master V6"]["promo_code"] == "SAVE20"
    assert coverage["Master V5"]["promo_code"] == "SAVE20"
    assert coverage["Pause M10"]["promo_code"] == "SAVE30"
    assert coverage["Pause M10"]["coverage_pct"] == 60.0
    assert coverage["Master S4"]["coverage_pct"] == 4.0
    assert coverage["Master V6"]["coverage_pct"] == 0.0

    none_row = next(row for row in summary["promotion_coverage"] if row.get("product") is None)
    standing_sum = sum(
        row["customers"]
        for row in summary["promotion_coverage"]
        if row.get("product") in ACTIVE_STANDING_PROMOTION_ORDER
    )
    assert none_row["promo_code"] == "None Promotion Target"
    assert none_row["customers"] == 200_000 - standing_sum
    assert none_row["coverage_pct"] == round(none_row["customers"] / 200_000 * 100, 1)


def test_promotion_coverage_uses_post_promo_price_response():
    import app.commercial.summary as summary_mod

    cohort = [
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
    original_loader = summary_mod.load_promo_coverage_cohort_rows
    summary_mod.load_promo_coverage_cohort_rows = lambda db, upload_id: cohort
    try:
        summary = build_commercial_intelligence_summary(
            db=_mock_db(),
            upload_id=None,
            product_rows=[
                {"product": "Master V6", "customers": 100_000, "revenue": 1.0, "share_pct": 50.0},
                {"product": "Master V5", "customers": 10_000, "revenue": 1.0, "share_pct": 5.0},
            ],
            expected_revenue=0.0,
            expected_orders=0.0,
            le_frame_incentive=0.0,
            targetable_customers=200_000,
        )
    finally:
        summary_mod.load_promo_coverage_cohort_rows = original_loader

    coverage = {row["product"]: row for row in summary["promotion_coverage"] if row.get("product")}
    assert coverage["Master V5"]["kpi_basis"] == "post_promo_price_response"
    assert coverage["Master V5"]["customers"] >= 100_000
    assert coverage["Master V5"]["down_convert"] >= 50_000
    assert coverage["Master V6"]["up_convert"] >= 40_000


def test_promotion_coverage_merges_legacy_pause_s4_into_master_s4():
    product_rows = [
        {"product": "Master S4", "customers": 50_000, "revenue": 5_000_000, "share_pct": 20.0},
        {"product": "Pause S4", "customers": 8_000, "revenue": 500_000, "share_pct": 2.0},
        {"product": "Master V6", "customers": 100_000, "revenue": 8_000_000, "share_pct": 40.0},
    ]
    summary = build_commercial_intelligence_summary(
        db=_mock_db(),
        upload_id=None,
        product_rows=product_rows,
        expected_revenue=0.0,
        expected_orders=0.0,
        le_frame_incentive=0.0,
        targetable_customers=200_000,
    )
    promos = {row["product"]: row for row in summary["active_promotions"]}
    assert "Pause S4" not in promos
    assert promos["Master S4"]["promo_code"] == "SAVE30"
    assert promos["Master S4"]["default_promotion_pct"] == 30.0

    coverage = {row["product"]: row for row in summary["promotion_coverage"] if row.get("product")}
    assert "Pause S4" not in coverage
    assert coverage["Master S4"]["customers"] >= 58_000
    assert coverage["Master S4"]["promo_code"] == "SAVE30"


def test_standing_promo_outreach_maps_non_promo_skus():
    from app.campaign.standing_promo_demand import standing_promo_outreach_product

    assert standing_promo_outreach_product("Master V9") == "Master V6"
    assert standing_promo_outreach_product("Master V7") == "Master V6"
    assert standing_promo_outreach_product("Master S4") == "Master S4"
    assert (
        standing_promo_outreach_product(
            "Master V9",
            purchase_power="Low",
            ceragem_segment="Mid-Low + Pain Index",
        )
        == "Master V5"
    )
    assert (
        standing_promo_outreach_product(
            "Master V9",
            purchase_power="Medium",
            ceragem_segment="Mid-High + Wellness",
        )
        == "Master V6"
    )
    assert standing_promo_outreach_product("Pause M10") == "Pause M10"
    assert standing_promo_outreach_product("Master V6") == "Master V6"


def test_pick_highest_conversion_opportunity_prefers_accessible_v_series():
    from app.campaign.standing_promo_demand import pick_highest_conversion_opportunity

    class _FakeDb:
        pass

    segments = [
        {"segment": "Mid-Low + Pain Index", "customers": 1_500_000, "conversion": 0.0029},
        {"segment": "Mid-High + Wellness", "customers": 300_000, "conversion": 0.0066},
        {"segment": "Mid-Low + Wellness", "customers": 700_000, "conversion": 0.0031},
    ]
    pp = {"high": 4, "medium": 37, "low": 59}
    product_rows = [{"product": "Pause M10", "customers": 866_000, "revenue": 25_000_000.0}]
    picked = pick_highest_conversion_opportunity(_FakeDb(), None, product_rows, segments, pp, 2_600_000)
    assert picked is not None
    assert picked["product"] in {"Master V6", "Master V5", "Master S4"}


def test_build_standing_promo_opportunity_rows_merges_actual_and_projected():
    from app.campaign.standing_promo_demand import build_standing_promo_opportunity_rows

    class _FakeDb:
        pass

    rows = build_standing_promo_opportunity_rows(
        _FakeDb(),
        None,
        [
            {"product": "Pause M10", "customers": 100, "revenue": 1_000_000.0},
            {"product": "Master V9", "customers": 50, "revenue": 500_000.0},
        ],
    )
    assert rows
    assert rows[0]["product"] == "Pause M10"
    assert rows[0]["customers"] == 100


if __name__ == "__main__":
    test_standing_promotion_catalog_matches_operating_plan()
    test_net_margin_matches_commercial_sheet()
    test_default_promotion_amount_only_for_standing_skus()
    test_promotion_fit_only_for_standing_skus()
    test_commercial_summary_active_promotions_list()
    test_promotion_coverage_is_per_standing_sku_not_merged_promo_code()
    test_standing_promo_outreach_maps_non_promo_skus()
    test_pick_highest_conversion_opportunity_prefers_accessible_v_series()
    test_build_standing_promo_opportunity_rows_merges_actual_and_projected()
    test_catalog_policy_strips_non_standing_promotions()
    print("test_standing_promotions: OK")
