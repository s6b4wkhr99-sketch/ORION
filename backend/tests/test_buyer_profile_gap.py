"""Tests for buyer profile GAP helpers."""

from app.campaign.buyer_profile_gap import (
    distribution_gap,
    state_tier,
)


def test_state_tier_ca():
    assert state_tier("CA") == "CA"
    assert state_tier("TX") == "PRIORITY"
    assert state_tier("OH") == "REST_US"
    assert state_tier("ON") == "OTHER"


def test_distribution_gap():
    gap = distribution_gap({"V4": 48.0, "V9": 2.0}, {"V4": 15.0, "V9": 22.0})
    assert gap["V4"]["gap_points"] == 33.0
    assert gap["V9"]["gap_points"] == -20.0
