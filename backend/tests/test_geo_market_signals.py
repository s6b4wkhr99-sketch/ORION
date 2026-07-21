"""Geographic market signal tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.geo.geo_market_signals import (
    brand_geo_boost,
    build_geo_market_signals,
    customer_brand_enclave_match,
    customer_sleep_deprivation_match,
    digital_geo_boost,
    pain_geo_boost,
    sleep_geo_boost,
)


def test_nyc_pain_and_digital_boost():
    signals = build_geo_market_signals(zip_code="10001", state="NY", city="New York", population=45000)
    assert signals["metro_tier"] == "tier1"
    assert signals["pain_geo_boost"] >= 0.14
    assert signals["digital_geo_boost"] >= 0.2


def test_korean_enclave_brand_boost():
    signals = build_geo_market_signals(zip_code="07650", state="NJ", city="Palisades Park", population=12000)
    assert signals["brand_geo_boost"] >= 0.2
    assert signals["brand_enclave_match"] is True


def test_tx_korean_corridor_plano():
    signals = brand_geo_boost(zip_code="75035", state="TX", city="Plano")
    assert signals["brand_geo_boost"] >= 0.22
    assert customer_brand_enclave_match(zip_code="75035", state="TX", city="Plano")


def test_pa_chinese_corridor_philadelphia():
    signals = brand_geo_boost(zip_code="19107", state="PA", city="Philadelphia")
    assert signals["brand_geo_boost"] >= 0.30
    assert customer_brand_enclave_match(zip_code="19107", state="PA", city="Philadelphia")


def test_tx_katy_suburban_growth_zip():
    signals = brand_geo_boost(zip_code="77494", state="TX", city="Katy")
    assert signals["brand_geo_boost"] >= 0.20


def test_rural_pain_access_proxy():
    pain = pain_geo_boost(zip_code="59001", state="MT", city="Absarokee", population=1200)
    assert pain["pain_geo_boost"] >= 0.04


def test_houston_tier2_digital_boost():
    signals = digital_geo_boost(zip_code="77002", state="TX", city="Houston")
    assert signals["digital_geo_boost"] >= 0.14
    assert signals["digital_metro_tier"] == "tier1"


def test_rural_montana_no_digital_boost():
    signals = digital_geo_boost(zip_code="59001", state="MT", city="Absarokee")
    assert signals["digital_geo_boost"] == 0.0
    assert signals["digital_metro_tier"] == "other"


def test_philadelphia_tier1_sleep_deprivation():
    signals = sleep_geo_boost(state="PA", city="Philadelphia")
    assert signals["sleep_geo_boost"] == 0.28
    assert signals["sleep_deprivation_tier"] == "tier1_sleep_deprived"
    assert customer_sleep_deprivation_match(state="PA", city="Philadelphia")


def test_san_antonio_tier2_sleep_deprivation():
    signals = sleep_geo_boost(state="TX", city="San Antonio")
    assert signals["sleep_geo_boost"] == 0.16
    assert signals["sleep_deprivation_tier"] == "tier2_sleep_deprived"


def test_houston_not_sleep_deprived_tier():
    signals = sleep_geo_boost(state="TX", city="Houston")
    assert signals["sleep_geo_boost"] == 0.0
    assert signals["sleep_deprivation_match"] is False


def test_las_vegas_chronic_pain_capital():
    pain = pain_geo_boost(zip_code=None, state="NV", city="Las Vegas", population=50000)
    assert pain["pain_geo_boost"] >= 0.20
    assert float(pain["chronic_pain_state_score"]) >= 95


def test_madison_back_care_friendly_moderates_boost():
    pain = pain_geo_boost(zip_code=None, state="WI", city="Madison", population=25000)
    assert pain["pain_geo_boost"] < 0.14


if __name__ == "__main__":
    test_nyc_pain_and_digital_boost()
    test_korean_enclave_brand_boost()
    test_tx_korean_corridor_plano()
    test_pa_chinese_corridor_philadelphia()
    test_tx_katy_suburban_growth_zip()
    test_rural_pain_access_proxy()
    test_houston_tier2_digital_boost()
    test_rural_montana_no_digital_boost()
    test_philadelphia_tier1_sleep_deprivation()
    test_san_antonio_tier2_sleep_deprivation()
    test_houston_not_sleep_deprived_tier()
    test_las_vegas_chronic_pain_capital()
    test_madison_back_care_friendly_moderates_boost()
    print("ok")
