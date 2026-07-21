"""Standing-promo outreach rollups for maps and sellable product views."""

from __future__ import annotations

from app.campaign.standing_promo_demand import (
    accumulate_product_metrics,
    accumulate_product_rollups,
    product_metrics_keys,
)


def test_product_metrics_keys_includes_outreach_target():
    assert product_metrics_keys("Pause M6") == ("Pause M6", "Pause M6s")
    assert product_metrics_keys("Master V9") == ("Master V9", "Master V6")
    assert product_metrics_keys("Pause M10") == ("Pause M10",)


def test_accumulate_product_metrics_rolls_m6_into_m6s():
    bucket: dict[str, dict] = {}
    accumulate_product_metrics(bucket, "Pause M6", customers=10, revenue=5000.0, orders=2.0)
    assert bucket["Pause M6"]["target_customers"] == 10
    assert bucket["Pause M6s"]["target_customers"] == 10
    assert bucket["Pause M6s"]["expected_revenue"] == 5000.0


def test_accumulate_product_rollups_for_dashboards():
    bucket: dict[str, dict] = {}
    accumulate_product_rollups(bucket, "Pause M6", customers=3, revenue=900.0, orders=1.0)
    accumulate_product_rollups(bucket, "Pause M6s", customers=1, revenue=100.0, orders=0.2)
    assert bucket["Pause M6s"]["customers"] == 4
    assert bucket["Pause M6s"]["revenue"] == 1000.0
