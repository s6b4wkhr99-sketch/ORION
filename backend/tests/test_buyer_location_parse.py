"""Tests for legacy LOCATION state parsing."""

from app.campaign.buyer_profile_gap import parse_legacy_location, parse_state_from_address, parse_us_state


def test_legacy_ca_dash_city():
    assert parse_us_state("CA - Los Angeles", source="legacy") == "CA"


def test_legacy_california_name():
    assert parse_us_state("California", source="legacy") == "CA"


def test_legacy_city_hint():
    assert parse_us_state("Torrance Showroom", source="legacy") == "CA"


def test_legacy_address_parsing():
    assert parse_state_from_address("1179 Alta Mesa dr. Brea, CA 92821") == "CA"


def test_legacy_store_location_with_address():
    assert parse_legacy_location("Los Cerritos Center", "1179 Alta Mesa dr. Brea, CA 92821") == "CA"


def test_legacy_store_fallback():
    assert parse_legacy_location("Brea Mall", None) == "CA"
