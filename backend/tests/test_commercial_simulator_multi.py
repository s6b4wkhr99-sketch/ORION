from app.commercial.simulator import simulate_commercial_multi


def test_simulate_commercial_multi_single_sku():
    result = simulate_commercial_multi(["Master V7"], target_customers=1000)
    assert result["multi_sku"] is False
    assert result["products"] == ["Master V7"]
    assert result["target_customers"] == 1000


def test_simulate_commercial_multi_aggregate():
    result = simulate_commercial_multi(
        ["Master V7", "Master S4"],
        target_customers=10000,
    )
    assert result["multi_sku"] is True
    assert result["products"] == ["Master V7", "Master S4"]
    assert len(result["by_product"]) == 2
    assert result["expected_orders"] == round(
        sum(row["expected_orders"] for row in result["by_product"]),
        2,
    )
    assert result["revenue_forecast"] == round(
        sum(row["revenue_forecast"] for row in result["by_product"]),
        2,
    )


def test_simulate_commercial_multi_preserves_conversion_override():
    result = simulate_commercial_multi(
        ["Master V7", "Master S4"],
        target_customers=10000,
        conversion_rate=0.0000025,
    )
    assert result["conversion_prediction"] == 0.0000025


def test_simulate_commercial_multi_layers_additional_promotion():
    baseline = simulate_commercial_multi(["Master V7", "Master S4"], target_customers=1000)
    with_extra = simulate_commercial_multi(
        ["Master V7", "Master S4"],
        target_customers=1000,
        additional_promotion_max=200,
        additional_promotion_pct=0.05,
    )
    assert with_extra["recommended_promotion"] >= baseline["recommended_promotion"]
    for row in with_extra["by_product"]:
        base_row = next(item for item in baseline["by_product"] if item["product"] == row["product"])
        assert row["recommended_promotion"] >= base_row["recommended_promotion"]


def test_simulate_commercial_multi_uses_upload_sku_target_mix():
    result = simulate_commercial_multi(
        ["Master V7", "Master S4"],
        target_customers=9999,
        target_customers_by_sku=[
            {"sku": "Master V7", "count": 3200},
            {"sku": "Master S4", "count": 1800},
        ],
    )
    assert result["target_customers"] == 5000
    by_sku = {row["product"]: row for row in result["by_product"]}
    assert by_sku["Master V7"]["target_customers"] == 3200
    assert by_sku["Master S4"]["target_customers"] == 1800
    assert result["expected_orders"] == round(
        sum(row["expected_orders"] for row in result["by_product"]),
        2,
    )


def test_simulate_commercial_multi_uses_promo_code_mapped_targets():
    # SAVE20 -> Master V6, SAVE30 -> Master S4 in standing promo catalog
    result = simulate_commercial_multi(
        ["Master V6", "Master S4"],
        target_customers=9999,
        target_customers_by_sku=[
            {"sku": "Master V6", "count": 220227},
            {"sku": "Master S4", "count": 393852},
        ],
    )
    assert result["target_customers"] == 614079
    by_sku = {row["product"]: row for row in result["by_product"]}
    assert by_sku["Master V6"]["target_customers"] == 220227
    assert by_sku["Master S4"]["target_customers"] == 393852
