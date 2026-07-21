"""Apply geographic market intelligence to customer context."""

from __future__ import annotations

from app.geo.geo_market_signals import build_geo_market_signals
from app.intelligence.types import IntelligenceContext


def apply_geo_market_intelligence(ctx: IntelligenceContext) -> None:
    """Attach metro / enclave / density signals used by Pain, Brand, Digital, and Forecast engines."""
    zip_intel = ctx.zip_intelligence or {}
    reference = zip_intel.get("reference") or ctx.zip_ref or {}
    city = zip_intel.get("city") or reference.get("city") or ctx.customer.get("city")
    state = ctx.customer.get("state") or zip_intel.get("state_intelligence") or reference.get("state")
    population = zip_intel.get("population") or reference.get("population")
    zip_code = zip_intel.get("normalized_zip") or ctx.customer.get("zip")

    signals = build_geo_market_signals(
        zip_code=zip_code,
        state=state,
        city=city,
        population=population,
    )
    ctx.zip_intelligence = {**zip_intel, **signals}

    ctx.add_trace(
        "Rule-GEO",
        "Geographic Market Intelligence",
        {"zip": zip_code, "state": state, "city": city, "population": population},
        signals,
        "Metro density, brand enclave, and digital-commerce geographic weights.",
    )
