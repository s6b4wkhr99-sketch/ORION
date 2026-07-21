"""Executive dashboard live aggregate tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.campaign.executive_dashboard import _product_series_code, build_executive_dashboard
from app.database import SessionLocal


def test_executive_dashboard_shape():
    db = SessionLocal()
    try:
        result = build_executive_dashboard(db)
    finally:
        db.close()

    assert result["data_source"] == "live"
    for key in (
        "total_customers",
        "state_performance",
        "radar_opportunities",
        "top_zips",
        "segment_performance",
        "product_distribution",
        "revenue_over_time",
        "top_campaigns",
        "intelligence_radar",
        "intelligence_score_distribution",
        "ceragem_distribution",
        "recent_activity",
        "system_status",
    ):
        assert key in result, f"missing {key}"

    assert isinstance(result["state_performance"], list)
    assert isinstance(result["radar_opportunities"], list)
    if result["radar_opportunities"]:
        sample = result["radar_opportunities"][0]
        for field in ("id", "state", "product", "opportunity_score", "customers", "revenue"):
            assert field in sample, f"radar_opportunities missing {field}"
        by_product: dict[str, set[str]] = {}
        for row in result["radar_opportunities"]:
            by_product.setdefault(row["product"], set()).add(row["state"])
        for product in ("Master V6", "Master V5", "Master V7", "Master V9", "Pause S4", "Pause M6s"):
            assert product in by_product, f"missing radar opportunities for {product}"
            assert len(by_product[product]) <= 10
    assert isinstance(result["intelligence_radar"], list)
    assert isinstance(result["ceragem_distribution"], list)
    if result["ceragem_distribution"]:
        sample = result["ceragem_distribution"][0]
        for field in ("segment", "customers", "pct", "revenue", "products"):
            assert field in sample, f"ceragem_distribution missing {field}"
    if result["intelligence_radar"]:
        axes = [item["axis"] for item in result["intelligence_radar"]]
        assert axes == [
            "Purchase Power",
            "Pain Index",
            "Lifestyle",
            "PRIZM Proxy",
            "Ceragem Segment",
            "Recommendation",
        ], axes
    assert len(result["system_status"]) >= 1

    if result["total_customers"] > 0:
        assert result["expected_revenue"] >= 0
        top_zips = result.get("top_zips") or []
        assert len(top_zips) <= 6
        if top_zips:
            tx_count = sum(1 for z in top_zips if z.get("state") == "TX")
            assert tx_count <= 1, f"TX should not dominate recent opportunities (got {tx_count})"
            assert len({z.get("state") for z in top_zips}) >= min(3, len(top_zips))
            for z in top_zips:
                assert z.get("intelligence_product"), "top_zips should expose ZIP-level intelligence_product"
                assert z.get("promo_outreach_product"), "top_zips should expose standing-promo outreach SKU"
            if len(top_zips) >= 3:
                series = {
                    _product_series_code(z.get("intelligence_product"))
                    for z in top_zips
                }
                assert len(series) >= 2, f"top_zips should span multiple product series (got {series})"
        print(
            f"PASS: executive dashboard — customers={result['total_customers']} "
            f"revenue={result['expected_revenue']:.2f} states={len(result['state_performance'])} "
            f"top_zips={len(top_zips)}"
        )
    else:
        print("PASS: executive dashboard shape (empty database)")


if __name__ == "__main__":
    test_executive_dashboard_shape()
