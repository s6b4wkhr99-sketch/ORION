"""TAM / TOM market sizing for state and metro intelligence views."""

from __future__ import annotations

# Category adoption: US households with massage/wellness chair purchase intent (proxy).
CATEGORY_HOUSEHOLD_RATE = 0.118
PERSONS_PER_HOUSEHOLD = 2.54
AVG_ORDER_VALUE_DEFAULT = 6_130.0
CERAGEM_FIT_BASE = 0.42
PURCHASE_POWER_ACCESS = {"High": 0.82, "Medium": 0.58, "Low": 0.31}


def _fit_rate_from_segments(ceragem_counts: dict[str, int]) -> float:
    if not ceragem_counts:
        return CERAGEM_FIT_BASE
    total = sum(ceragem_counts.values()) or 1
    weighted = 0.0
    weights = {
        "High + Wellness": 0.55,
        "High + Pain Index": 0.92,
        "Mid-High + Wellness": 0.78,
        "Mid-High + Pain Index": 0.95,
        "Mid-Low + Wellness": 0.62,
        "Mid-Low + Pain Index": 0.88,
    }
    for segment, count in ceragem_counts.items():
        weighted += (count / total) * weights.get(segment, CERAGEM_FIT_BASE)
    return min(0.98, max(0.15, weighted))


def _dominant_pp_band(pp_counts: dict[str, int]) -> str:
    if not pp_counts:
        return "Medium"
    return max(pp_counts.items(), key=lambda item: item[1])[0]


def compute_market_sizing(
    *,
    population: int | None,
    target_customers: int,
    expected_revenue: float,
    expected_orders: float,
    ceragem_segments: dict[str, int] | None = None,
    purchase_power_bands: dict[str, int] | None = None,
    avg_order_value: float | None = None,
) -> dict:
    """Compute TAM/TOM/SAM from geography population + cohort intelligence."""
    pop = max(population or 0, target_customers * 8, 1)
    households = pop / PERSONS_PER_HOUSEHOLD
    tam_households = round(households * CATEGORY_HOUSEHOLD_RATE)
    aov = avg_order_value or (expected_revenue / expected_orders if expected_orders else AVG_ORDER_VALUE_DEFAULT)
    tam_revenue = round(tam_households * aov, 2)

    fit_rate = _fit_rate_from_segments(ceragem_segments or {})
    pp_band = _dominant_pp_band(purchase_power_bands or {})
    access = PURCHASE_POWER_ACCESS.get(pp_band, PURCHASE_POWER_ACCESS["Medium"])
    tom_households = round(tam_households * fit_rate * access)
    avg_customer_revenue = expected_revenue / target_customers if target_customers else aov * 0.0038
    tom_revenue = round(tom_households * avg_customer_revenue, 2)

    sam_customers = target_customers
    penetration = round(sam_customers / tom_households, 4) if tom_households else 0.0
    conversion = expected_orders / target_customers if target_customers else 0.0

    return {
        "tam_households": tam_households,
        "tam_population": int(pop),
        "tam_revenue_potential": tam_revenue,
        "tom_households": tom_households,
        "tom_revenue_potential": tom_revenue,
        "sam_customers": sam_customers,
        "penetration_pct": penetration,
        "expected_conversion_rate": round(conversion, 6),
        "avg_order_value": round(aov, 2),
        "ceragem_fit_rate": round(fit_rate, 4),
        "purchase_power_access_rate": access,
        "methodology": "ACS population × category adoption × Ceragem segment fit × purchase-power access",
        "data_vintage": "2022-acs",
    }
