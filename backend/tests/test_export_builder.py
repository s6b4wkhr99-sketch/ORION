"""Export CSV row building — target SKU / recommended product population."""

from __future__ import annotations

from types import SimpleNamespace

from app.providers.export_builder import build_export_row_dict


def test_export_row_includes_target_sku_and_recommended_product():
    customer = SimpleNamespace(
        email="buyer@example.com",
        first_name="Buyer",
        last_name="One",
        phone="",
        address="",
        city="",
        state="CA",
        zip="90210",
        permission="Opt-In",
    )
    intel = SimpleNamespace(
        recommended_product="Master S4",
        promo_code="SAVE30",
        recommended_promotion=1200.0,
        price_resistance_score=0.42,
        commercial_version="2026.07",
        prizm_proxy_segment="Wellness Seekers",
        ceragem_segment="Wellness Seekers",
        message_direction="",
    )
    headers = [
        ("email_address", "Email Address"),
        ("intel_recommended_product", "Recommended Product"),
        ("target_sku", "Target SKU"),
        ("promo_code", "Promo Code"),
        ("campaign_id", "Campaign ID"),
        ("campaign_name", "Campaign Name"),
    ]

    row = build_export_row_dict(
        headers,
        campaign_id="AUD-ABC12345",
        campaign_name="Opportunity · Master S4 · National",
        customer=customer,
        intel=intel,
    )

    assert row["Recommended Product"] == "Master S4"
    assert row["Target SKU"] == "Master S4"
    assert row["Promo Code"] == "SAVE30"
    assert row["Email Address"] == "buyer@example.com"
