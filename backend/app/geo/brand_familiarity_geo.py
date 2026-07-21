"""
Brand Familiarity v4 — census-based Asian density + ACS Korean metro tiers.

Sources:
- US Asian alone baseline 5.9%: https://www.indexmundi.com/facts/united-states/quick-facts
- City Asian % rankings: https://www.indexmundi.com/facts/united-states/quick-facts/cities/rank/asian-population-percentage
- Korean metro/state population (ACS 2022): https://unitedkoreans.com/미국-도시별-한인-인구-순위/
"""

from __future__ import annotations

from dataclasses import dataclass

# US national Asian alone, percent (Census QuickFacts via IndexMundi).
US_ASIAN_ALONE_BASELINE_PCT = 5.9

# Selected cities from IndexMundi top-100 Asian % + CIOS customer corridors (Census ACS estimates).
CITY_ASIAN_ALONE_PCT: dict[tuple[str, str], float] = {
    ("HI", "HONOLULU"): 42.9,
    ("CA", "FREMONT"): 63.8,
    ("CA", "IRVINE"): 43.2,
    ("CA", "SANTA CLARA"): 41.0,
    ("CA", "SUNNYVALE"): 40.9,
    ("CA", "DALY CITY"): 59.7,
    ("CA", "SAN FRANCISCO"): 34.1,
    ("CA", "LOS ANGELES"): 11.6,
    ("CA", "KOREATOWN"): 11.6,
    ("CA", "FULLERTON"): 22.4,
    ("CA", "SAN JOSE"): 35.2,
    ("CA", "OAKLAND"): 15.2,
    ("CA", "RIVERSIDE"): 7.2,
    ("WA", "SEATTLE"): 15.4,
    ("WA", "BELLEVUE"): 28.5,
    ("WA", "FEDERAL WAY"): 24.1,
    ("NY", "NEW YORK"): 14.1,
    ("NY", "FLUSHING"): 14.1,
    ("NY", "BAYSIDE"): 14.1,
    ("NJ", "JERSEY CITY"): 26.9,
    ("NJ", "PALISADES PARK"): 57.0,
    ("NJ", "FORT LEE"): 42.5,
    ("NJ", "RIDGEFIELD"): 18.2,
    ("NJ", "LEONIA"): 26.0,
    ("TX", "PLANO"): 19.4,
    ("TX", "IRVING"): 15.8,
    ("TX", "CARROLLTON"): 14.6,
    ("TX", "RICHARDSON"): 16.2,
    ("TX", "FRISCO"): 18.0,
    ("TX", "MCKINNEY"): 12.5,
    ("TX", "GARLAND"): 10.8,
    ("TX", "ARLINGTON"): 7.5,
    ("TX", "LEWISVILLE"): 11.2,
    ("TX", "ALLEN"): 13.4,
    ("TX", "DALLAS"): 4.3,
    ("TX", "HOUSTON"): 6.9,
    ("TX", "KATY"): 6.9,
    ("TX", "SPRING"): 6.9,
    ("TX", "CYPRESS"): 6.9,
    ("TX", "SUGAR LAND"): 6.9,
    ("TX", "STAFFORD"): 6.9,
    ("TX", "MISSOURI CITY"): 6.9,
    ("TX", "PEARLAND"): 6.9,
    ("TX", "ROUND ROCK"): 8.2,
    ("PA", "PHILADELPHIA"): 8.0,
    ("PA", "PITTSBURGH"): 5.5,
    ("GA", "ATLANTA"): 5.2,
    ("GA", "DULUTH"): 12.5,
    ("GA", "SUWANEE"): 14.0,
    ("IL", "CHICAGO"): 6.9,
    ("IL", "NAPERVILLE"): 12.8,
    ("IL", "SCHAUMBURG"): 18.5,
    ("VA", "ANNANDALE"): 28.0,
    ("VA", "CENTREVILLE"): 22.0,
    ("VA", "ARLINGTON"): 10.2,
    ("VA", "ALEXANDRIA"): 7.8,
    ("MD", "BETHESDA"): 12.0,
    ("MD", "ROCKVILLE"): 15.5,
    ("DC", "WASHINGTON"): 10.5,
}


@dataclass(frozen=True)
class KoreanMetroRegion:
    key: str
    tier: int
    boost: float
    label: str
    cities: frozenset[tuple[str, str]]


# ACS 2022 Korean population metro TOP 10 (United Koreans / Census).
KOREAN_METRO_REGIONS: tuple[KoreanMetroRegion, ...] = (
    KoreanMetroRegion(
        key="la",
        tier=1,
        boost=0.18,
        label="Los Angeles metro",
        cities=frozenset(
            {
                ("CA", "LOS ANGELES"),
                ("CA", "KOREATOWN"),
                ("CA", "IRVINE"),
                ("CA", "FULLERTON"),
                ("CA", "GARDEN GROVE"),
                ("CA", "ANAHEIM"),
            }
        ),
    ),
    KoreanMetroRegion(
        key="ny_nj",
        tier=1,
        boost=0.18,
        label="New York / NJ metro",
        cities=frozenset(
            {
                ("NY", "NEW YORK"),
                ("NY", "FLUSHING"),
                ("NY", "BAYSIDE"),
                ("NJ", "PALISADES PARK"),
                ("NJ", "FORT LEE"),
                ("NJ", "RIDGEFIELD"),
                ("NJ", "LEONIA"),
                ("NJ", "ENGLEWOOD CLIFFS"),
            }
        ),
    ),
    KoreanMetroRegion(
        key="dc",
        tier=1,
        boost=0.18,
        label="Washington DC metro",
        cities=frozenset(
            {
                ("DC", "WASHINGTON"),
                ("VA", "ANNANDALE"),
                ("VA", "CENTREVILLE"),
                ("VA", "ARLINGTON"),
                ("VA", "ALEXANDRIA"),
                ("VA", "FAIRFAX"),
                ("MD", "BETHESDA"),
                ("MD", "ROCKVILLE"),
                ("MD", "SILVER SPRING"),
            }
        ),
    ),
    KoreanMetroRegion(
        key="seattle",
        tier=2,
        boost=0.12,
        label="Seattle metro",
        cities=frozenset(
            {
                ("WA", "SEATTLE"),
                ("WA", "FEDERAL WAY"),
                ("WA", "BELLEVUE"),
                ("WA", "KIRKLAND"),
                ("WA", "LYNNWOOD"),
            }
        ),
    ),
    KoreanMetroRegion(
        key="chicago",
        tier=2,
        boost=0.12,
        label="Chicago metro",
        cities=frozenset(
            {
                ("IL", "CHICAGO"),
                ("IL", "NAPERVILLE"),
                ("IL", "SCHAUMBURG"),
                ("IL", "GLENVIEW"),
            }
        ),
    ),
    KoreanMetroRegion(
        key="san_francisco",
        tier=2,
        boost=0.12,
        label="San Francisco metro",
        cities=frozenset(
            {
                ("CA", "SAN FRANCISCO"),
                ("CA", "DALY CITY"),
                ("CA", "FREMONT"),
                ("CA", "SUNNYVALE"),
                ("CA", "SANTA CLARA"),
                ("CA", "SAN JOSE"),
            }
        ),
    ),
    KoreanMetroRegion(
        key="atlanta",
        tier=2,
        boost=0.12,
        label="Atlanta metro",
        cities=frozenset(
            {
                ("GA", "ATLANTA"),
                ("GA", "DULUTH"),
                ("GA", "SUWANEE"),
                ("GA", "JOHNS CREEK"),
            }
        ),
    ),
    KoreanMetroRegion(
        key="philadelphia",
        tier=3,
        boost=0.08,
        label="Philadelphia metro",
        cities=frozenset(
            {
                ("PA", "PHILADELPHIA"),
                ("PA", "NORRISTOWN"),
                ("PA", "LEVITTOWN"),
            }
        ),
    ),
    KoreanMetroRegion(
        key="dallas",
        tier=3,
        boost=0.08,
        label="Dallas metro",
        cities=frozenset(
            {
                ("TX", "DALLAS"),
                ("TX", "PLANO"),
                ("TX", "IRVING"),
                ("TX", "CARROLLTON"),
                ("TX", "RICHARDSON"),
                ("TX", "FRISCO"),
                ("TX", "MCKINNEY"),
                ("TX", "GARLAND"),
                ("TX", "ARLINGTON"),
                ("TX", "LEWISVILLE"),
                ("TX", "ALLEN"),
            }
        ),
    ),
    KoreanMetroRegion(
        key="riverside",
        tier=3,
        boost=0.08,
        label="Riverside metro",
        cities=frozenset({("CA", "RIVERSIDE"), ("CA", "CORONA")}),
    ),
    KoreanMetroRegion(
        key="houston",
        tier=3,
        boost=0.08,
        label="Houston metro (TX Korean corridor)",
        cities=frozenset(
            {
                ("TX", "HOUSTON"),
                ("TX", "KATY"),
                ("TX", "SPRING"),
                ("TX", "CYPRESS"),
                ("TX", "SUGAR LAND"),
                ("TX", "STAFFORD"),
                ("TX", "MISSOURI CITY"),
                ("TX", "PEARLAND"),
            }
        ),
    ),
)

# ACS 2022 state Korean population TOP 10 (>= 55k).
KOREAN_STATE_HIGH_POPULATION: frozenset[str] = frozenset(
    {"CA", "NY", "TX", "NJ", "WA", "VA", "GA", "IL", "MD", "HI"}
)
KOREAN_STATE_BOOST = 0.06

ASIAN_TIER_BOOSTS: tuple[tuple[float, float, str], ...] = (
    (4.0, 0.20, "tier1_asian_density"),
    (2.5, 0.14, "tier2_asian_density"),
    (1.5, 0.08, "tier3_asian_density"),
)


def asian_city_signals(state_code: str, city_key: str) -> dict[str, float | str | bool]:
    """Asian alone % relative to US 5.9% baseline."""
    pct = CITY_ASIAN_ALONE_PCT.get((state_code, city_key))
    if pct is None:
        return {
            "asian_population_pct": 0.0,
            "asian_relative_index": 0.0,
            "asian_city_tier": "none",
            "asian_city_boost": 0.0,
            "asian_city_match": False,
        }

    relative = round(pct / US_ASIAN_ALONE_BASELINE_PCT, 2)
    boost = 0.0
    tier = "none"
    for threshold, tier_boost, tier_name in ASIAN_TIER_BOOSTS:
        if relative >= threshold:
            boost = tier_boost
            tier = tier_name
            break

    return {
        "asian_population_pct": pct,
        "asian_relative_index": relative,
        "asian_city_tier": tier,
        "asian_city_boost": boost,
        "asian_city_match": boost > 0,
    }


def korean_metro_signals(state_code: str, city_key: str) -> dict[str, float | str | bool]:
    """Korean population metro tier (ACS 2022 TOP 10 + Houston corridor)."""
    for region in KOREAN_METRO_REGIONS:
        if (state_code, city_key) in region.cities:
            return {
                "korean_metro_key": region.key,
                "korean_metro_label": region.label,
                "korean_metro_tier": f"tier{region.tier}",
                "korean_metro_boost": region.boost,
                "korean_metro_match": True,
            }
    return {
        "korean_metro_key": "none",
        "korean_metro_label": "",
        "korean_metro_tier": "none",
        "korean_metro_boost": 0.0,
        "korean_metro_match": False,
    }


def korean_state_signals(state_code: str, *, korean_metro_matched: bool) -> dict[str, float | str | bool]:
    """State-level Korean population boost when metro tier did not already match."""
    if korean_metro_matched or state_code not in KOREAN_STATE_HIGH_POPULATION:
        return {
            "korean_state_tier": "none",
            "korean_state_boost": 0.0,
            "korean_state_match": False,
        }
    return {
        "korean_state_tier": "acs_top10_state",
        "korean_state_boost": KOREAN_STATE_BOOST,
        "korean_state_match": True,
    }
