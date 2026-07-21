"""Priority US market state helpers."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.reference.market_priority import (
    M10_PREMIUM_STATES,
    normalize_customer_state,
    PRIORITY_MARKET_STATES,
    S4_VALUE_STATES,
)


def test_priority_markets_include_traditional_demand_states():
    assert PRIORITY_MARKET_STATES == frozenset(
        {"CA", "TX", "FL", "NY", "NJ", "VA", "DC", "IL", "PA", "MA"}
    )


def test_m10_premium_states():
    assert "CA" in M10_PREMIUM_STATES
    assert "TX" not in M10_PREMIUM_STATES


def test_s4_value_states():
    assert S4_VALUE_STATES == frozenset({"FL", "TX"})


def test_normalize_customer_state():
    assert normalize_customer_state("ca") == "CA"
    assert normalize_customer_state("District of Columbia") == "DC"
    assert normalize_customer_state(None) is None
