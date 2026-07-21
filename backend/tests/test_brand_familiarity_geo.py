"""Brand Familiarity v4 geo tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.geo.brand_familiarity_geo import (
    US_ASIAN_ALONE_BASELINE_PCT,
    asian_city_signals,
    korean_metro_signals,
)
from app.geo.geo_market_signals import brand_geo_boost, customer_brand_enclave_match


def test_us_asian_baseline_is_5_9_percent():
    assert US_ASIAN_ALONE_BASELINE_PCT == 5.9


def test_fremont_tier1_asian_density():
    signals = asian_city_signals("CA", "FREMONT")
    assert signals["asian_relative_index"] >= 4.0
    assert signals["asian_city_tier"] == "tier1_asian_density"
    assert signals["asian_city_boost"] == 0.20


def test_plano_tier2_asian_density():
    signals = asian_city_signals("TX", "PLANO")
    assert signals["asian_relative_index"] >= 2.5
    assert signals["asian_city_boost"] == 0.14


def test_dallas_korean_metro_tier3():
    signals = korean_metro_signals("TX", "DALLAS")
    assert signals["korean_metro_match"] is True
    assert signals["korean_metro_key"] == "dallas"
    assert signals["korean_metro_boost"] == 0.08


def test_katy_houston_korean_metro():
    signals = korean_metro_signals("TX", "KATY")
    assert signals["korean_metro_match"] is True
    assert signals["korean_metro_key"] == "houston"


def test_plano_brand_v4_combined_boost():
    signals = brand_geo_boost(zip_code="75035", state="TX", city="Plano")
    assert signals["brand_geo_boost"] >= 0.30
    assert signals["asian_city_match"] is True
    assert signals["korean_metro_match"] is True
    assert "tier2_asian_density" in signals["brand_geo_reasons"]
    assert "korean_metro_dallas" in signals["brand_geo_reasons"]


def test_philadelphia_asian_and_korean_layers():
    signals = brand_geo_boost(zip_code="19107", state="PA", city="Philadelphia")
    assert signals["brand_geo_boost"] >= 0.30
    assert signals["korean_metro_key"] == "philadelphia"
    assert customer_brand_enclave_match(zip_code="19107", state="PA", city="Philadelphia")


def test_palisades_park_high_asian_and_korean_ny_metro():
    signals = brand_geo_boost(zip_code="07650", state="NJ", city="Palisades Park")
    assert signals["asian_city_tier"] == "tier1_asian_density"
    assert signals["korean_metro_key"] == "ny_nj"
    assert signals["brand_geo_boost"] == 0.45


def test_state_affinity_follows_acs_korean_rank_not_tx_pa_hypothesis():
    from app.geo.geo_market_signals import STATE_BRAND_AFFINITY

    assert "PA" not in STATE_BRAND_AFFINITY
    assert STATE_BRAND_AFFINITY["CA"] > STATE_BRAND_AFFINITY["TX"]
    assert STATE_BRAND_AFFINITY["NY"] > STATE_BRAND_AFFINITY["TX"]
    assert STATE_BRAND_AFFINITY["NJ"] > STATE_BRAND_AFFINITY["TX"]

    ca_la = brand_geo_boost(zip_code=None, state="CA", city="Los Angeles")
    tx_houston = brand_geo_boost(zip_code=None, state="TX", city="Houston")
    assert ca_la["brand_geo_boost"] > tx_houston["brand_geo_boost"]
