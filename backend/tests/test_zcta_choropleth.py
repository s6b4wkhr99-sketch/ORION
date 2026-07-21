"""ZIP choropleth score key normalization."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.geo.zcta_choropleth import _compute_zip_scores


def test_compute_zip_scores_pads_leading_zero_zips():
    db = MagicMock()
    payload = {
        "zip_opportunity": [
            {
                "zip": "1201",
                "city": "Springfield",
                "expected_revenue": 1000.0,
                "target_customers": 10,
            },
            {
                "zip": "01741",
                "city": "Carlisle",
                "expected_revenue": 500.0,
                "target_customers": 5,
            },
        ]
    }
    with patch("app.geo.zcta_choropleth._get_state_dashboard", return_value=payload):
        with patch("app.geo.zcta_choropleth._compute_zip_product_scores", return_value={}):
            scores = _compute_zip_scores(db, None, "MA")

    assert "01201" in scores
    assert scores["01201"]["expected_revenue"] == 1000.0
    assert "01741" in scores
    assert scores["01741"]["expected_revenue"] == 500.0
    assert "1201" not in scores


def test_compute_zip_product_scores_normalizes_zip_keys():
    db = MagicMock()
    q = db.query.return_value.select_from.return_value.join.return_value.filter.return_value
    q.group_by.return_value.all.return_value = [
        ("1201", "Pause S4", 12, 2400.0),
        ("01741", "Master S4", 3, 900.0),
    ]
    from app.geo.zcta_choropleth import _compute_zip_product_scores

    with patch("app.intelligence.ladder_opportunity.aggregate_ladder_geo_product_opportunity", return_value={}):
        with patch("app.geo.zcta_choropleth._apply_geo_gated_m10_outreach_credit", side_effect=lambda _db, m: m):
            scores = _compute_zip_product_scores(db, None, "MA")
    assert "Pause S4" in scores["01201"]
    assert scores["01201"]["Pause S4"]["expected_revenue"] == 2400.0
    assert scores["01741"]["Master S4"]["target_customers"] == 3


def test_apply_geo_gated_m10_outreach_credit_skips_non_affluent_zip():
    from app.geo.zcta_choropleth import _apply_geo_gated_m10_outreach_credit

    db = MagicMock()
    zi = MagicMock()
    zi.zip = "90210"
    zi.top50_rank = False
    zi.median_income = 45000
    db.query.return_value.filter.return_value.all.return_value = [zi]

    merged = {
        "90210": {
            "Pause M6": {"expected_revenue": 500.0, "target_customers": 10},
        },
    }
    out = _apply_geo_gated_m10_outreach_credit(db, merged)
    assert "Pause M10" not in out["90210"]


def test_apply_geo_gated_m10_outreach_credit_credits_affluent_zip():
    from app.geo.zcta_choropleth import _apply_geo_gated_m10_outreach_credit

    db = MagicMock()
    zi = MagicMock()
    zi.zip = "90210"
    zi.top50_rank = True
    zi.median_income = 180000
    db.query.return_value.filter.return_value.all.return_value = [zi]

    merged = {
        "90210": {
            "Pause M6": {"expected_revenue": 500.0, "target_customers": 10},
            "Pause M6s": {"expected_revenue": 200.0, "target_customers": 4},
            "Master V9": {"expected_revenue": 5000.0, "target_customers": 50},
        },
    }
    out = _apply_geo_gated_m10_outreach_credit(db, merged)
    assert out["90210"]["Pause M10"]["expected_revenue"] == 700.0
    assert out["90210"]["Pause M10"]["target_customers"] == 14


def test_apply_geo_gated_m10_outreach_credit_includes_v7_in_affluent_zip():
    from app.geo.zcta_choropleth import _apply_geo_gated_m10_outreach_credit

    db = MagicMock()
    zi = MagicMock()
    zi.zip = "10021"
    zi.top50_rank = True
    zi.median_income = 220000
    db.query.return_value.filter.return_value.all.return_value = [zi]

    merged = {
        "10021": {
            "Master V7": {"expected_revenue": 1200.0, "target_customers": 20},
            "Master V9": {"expected_revenue": 9000.0, "target_customers": 80},
        },
    }
    out = _apply_geo_gated_m10_outreach_credit(db, merged)
    assert out["10021"]["Pause M10"]["expected_revenue"] == 1200.0
    assert out["10021"]["Pause M10"]["target_customers"] == 20
