"""Standing promo demand projection — shared radar/coverage logic."""

from __future__ import annotations

from app.campaign.standing_promo_demand import synthesize_standing_promo_cells


def test_synthesize_v6_from_donor_demand():
    cells = {
        ("TX", "Master V7"): {"state": "TX", "product": "Master V7", "customers": 1000, "orders": 10.0, "revenue": 50000.0},
        ("TX", "Master S4"): {"state": "TX", "product": "Master S4", "customers": 200, "orders": 2.0, "revenue": 8000.0},
    }
    synthesize_standing_promo_cells(cells, ["TX"])
    v6 = cells.get(("TX", "Master V6"))
    assert v6 is not None
    assert v6["customers"] > 0
    assert v6.get("synthetic") is True
    # 45% of 1000 from Master V7 donor (V4 donor removed — value SKU)
    assert v6["customers"] == 450


def test_synthesize_m10_all_states():
    cells = {
        ("TX", "Master V9"): {"state": "TX", "product": "Master V9", "customers": 500, "orders": 5.0, "revenue": 25000.0},
    }
    synthesize_standing_promo_cells(cells, ["TX"])
    m10 = cells.get(("TX", "Pause M10"))
    assert m10 is not None
    assert m10["customers"] == 175


def test_pad_geo_product_rows_fills_to_limit():
    from app.campaign.standing_promo_demand import pad_geo_product_rows

    buckets = {
        "Master V6": [{"city": "Austin", "revenue": 100.0, "customers": 10, "orders": 1.0}],
        "Master V9": [
            {"city": f"City-{i}", "revenue": float(200 - i), "customers": 5, "orders": 0.5}
            for i in range(30)
        ],
    }
    padded = pad_geo_product_rows(
        "Master V6",
        buckets["Master V6"],
        buckets,
        geo_field="city",
        limit=25,
    )
    assert len(padded) == 25
    assert padded[0]["city"] == "Austin"
    assert all(row.get("product") == "Master V6" for row in padded)


def test_synthesize_skips_when_actual_volume_exists():
    cells = {
        ("CA", "Master V6"): {"state": "CA", "product": "Master V6", "customers": 42, "orders": 1.0, "revenue": 2000.0},
        ("CA", "Master V7"): {"state": "CA", "product": "Master V7", "customers": 1000, "orders": 10.0, "revenue": 50000.0},
    }
    synthesize_standing_promo_cells(cells, ["CA"])
    assert cells[("CA", "Master V6")]["customers"] == 42


if __name__ == "__main__":
    test_synthesize_v6_from_donor_demand()
    test_synthesize_skips_when_actual_volume_exists()
    print("test_standing_promo_demand: OK")
