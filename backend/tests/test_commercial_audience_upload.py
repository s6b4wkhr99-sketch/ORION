"""Audience Export CSV → Commercial Simulator auto-analysis."""

from __future__ import annotations

import pytest

from app.commercial.audience_upload import analyze_audience_export_csv, parse_audience_export_csv


def _csv(*lines: str) -> bytes:
    return "\n".join(lines).encode("utf-8")


def test_parse_audience_export_from_campaign_name():
    content = _csv(
        "Email Address,State,Campaign Name,Campaign ID,Promo Code,Recommended Promotion",
        'a@test.com,CA,"Opportunity · Master V7 · CA · Jul 21, 2026",AUD-ABC12345,SAVE20,1500',
        'b@test.com,NY,"Opportunity · Master V7 · CA · Jul 21, 2026",AUD-ABC12345,SAVE20,1500',
    )
    parsed = parse_audience_export_csv(content)
    assert parsed["target_customers"] == 2
    assert parsed["product"] == "Master V7"
    assert parsed["campaign_id"] == "AUD-ABC12345"
    assert parsed["promo_code"] == "SAVE20"
    assert parsed["avg_promotion"] == 1500.0
    assert parsed["avg_selling_price"] is not None
    assert parsed["avg_selling_price"] > 0
    assert parsed["promo_code_mix"] == [{"promo_code": "SAVE20", "count": 2}]


def test_parse_audience_export_promo_code_mix_without_product_column():
    content = _csv(
        "Email Address,State,Campaign Name,Promo Code,Recommended Promotion",
        'a@test.com,CA,"Opportunity · Master V6 · National · Jul 21, 2026",SAVE30,0',
        'b@test.com,NY,"Opportunity · Master V6 · National · Jul 21, 2026",SAVE30,0',
        'c@test.com,TX,"Opportunity · Master V6 · National · Jul 21, 2026",SAVE20,1600',
    )
    parsed = parse_audience_export_csv(content)
    assert parsed["product"] == "Master V6"
    assert parsed["sku_mix"] == []
    assert parsed["promo_code_mix"] == [
        {"promo_code": "SAVE30", "count": 2},
        {"promo_code": "SAVE20", "count": 1},
    ]


def test_analyze_audience_export_runs_simulation():
    content = _csv(
        "Recommended Product,State,Campaign Name,Promo Code,Recommended Promotion",
        "Master S4,TX,Opportunity · Master S4 · TX · Jul 21, 2026,SPRING,800",
    )
    out = analyze_audience_export_csv(content)
    assert out["audience"]["product"] == "Master S4"
    assert out["simulation"]["simulation"] is True
    assert out["simulation"]["target_customers"] == 1
    assert out["simulation"]["revenue_forecast"] >= 0


def test_analyze_audience_export_honors_conversion_rate_override():
    content = _csv(
        "Recommended Product,State,Campaign Name,Promo Code,Recommended Promotion",
        "Master S4,TX,Opportunity · Master S4 · TX · Jul 21, 2026,SPRING,800",
        "Master S4,CA,Opportunity · Master S4 · CA · Jul 21, 2026,SPRING,800",
    )
    forced = analyze_audience_export_csv(content, conversion_rate=0.0000025)
    assert forced["simulation"]["conversion_prediction"] == 0.0000025


def test_parse_rejects_empty_csv():
    with pytest.raises(ValueError, match="no data rows"):
        parse_audience_export_csv(_csv("Email Address,State"))
