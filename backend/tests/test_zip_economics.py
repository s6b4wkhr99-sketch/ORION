"""ZIP economics baseline tests (unitedstateszipcodes.org / ACS B19013)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.geo.zip_economics import (
    build_zip_economics,
    economic_power_score,
    income_tier,
    purchase_potential_score,
)


def test_income_tiers_match_research_baseline():
    assert income_tier(250_001, premium_zip=False) == "High"
    assert income_tier(127_368, premium_zip=False) == "High"
    assert income_tier(85_000, premium_zip=False) == "Mid"
    assert income_tier(45_000, premium_zip=False) == "Lower"
    assert income_tier(None, premium_zip=True) == "High"


def test_purchase_potential_increases_with_affluence():
    lower = purchase_potential_score(42_000)
    mid = purchase_potential_score(85_000)
    high = purchase_potential_score(190_000, premium_zip=True)
    assert lower < mid < high


def test_build_zip_economics_includes_source_label():
    economics = build_zip_economics(127_368, premium_zip=False, income_vintage="ACS-2023-5yr")
    assert economics["income_source"] == "unitedstateszipcodes.org/ACS-B19013"
    assert economics["income_tier"] == "High"
    assert economics["economic_power_score"] == economic_power_score(127_368)


if __name__ == "__main__":
    test_income_tiers_match_research_baseline()
    test_purchase_potential_increases_with_affluence()
    test_build_zip_economics_includes_source_label()
    print("ok")
