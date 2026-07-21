"""Intelligence Engine Pipeline — Volume 04 Section 21 execution order."""

from collections.abc import Callable

from app.commercial.engine import (
    apply_zip_income_proxy,
    run_commercial_post_engine,
    run_commercial_pre_engine,
)
from app.intelligence.calculation_framework import apply_calculation_framework
from app.intelligence.ceragem import run_ceragem_segment_engine
from app.intelligence.datalogix_engine import run_datalogix_engine
from app.intelligence.forecasting import run_forecast_engine
from app.intelligence.geo_intelligence import apply_geo_market_intelligence
from app.intelligence.lifestyle import run_lifestyle_engine
from app.intelligence.message_direction import run_message_direction_engine
from app.intelligence.normalization import run_normalization_engine
from app.intelligence.pain_index import run_pain_index_engine
from app.intelligence.prizm import run_prizm_proxy_engine
from app.intelligence.purchase_power import run_purchase_power_engine
from app.intelligence.recommendation import run_recommendation_engine
from app.intelligence.sleep_segmentation import apply_sleep_segment_intelligence
from app.intelligence.types import IntelligenceContext
from app.intelligence.zip_engine import run_zip_intelligence_engine


def run_intelligence_pipeline(
    *,
    customer: dict,
    datalogix_raw: dict,
    zip_lookup: Callable[[str], dict | None] | None = None,
    zip_ref: dict | None = None,
    row: dict | None = None,
    headers: list[str] | None = None,
    column_map: dict[str, str | None] | None = None,
    filename_state: str | None = None,
) -> IntelligenceContext:
    """
    Section 21 Intelligence Processing Summary:
    Normalization → Datalogix → ZIP → PRIZM → Purchase Power → Pain → Lifestyle
    → Ceragem Segment → Message Direction → Recommendation → Revenue Forecast
    """
    ctx = IntelligenceContext(customer=dict(customer), datalogix_raw=dict(datalogix_raw), zip_ref=zip_ref)

    try:
        if row is not None and headers is not None and column_map is not None:
            run_normalization_engine(ctx, row, headers, column_map, filename_state)
            customer.update({k: v for k, v in ctx.customer.items() if v is not None})

        run_datalogix_engine(ctx)
        run_zip_intelligence_engine(ctx, zip_lookup=zip_lookup)
        apply_geo_market_intelligence(ctx)
        apply_zip_income_proxy(ctx)

        ctx.prizm_proxy_segment = run_prizm_proxy_engine(ctx)

        run_purchase_power_engine(ctx)
        run_pain_index_engine(ctx)
        run_lifestyle_engine(ctx)

        ctx.ceragem_segment = run_ceragem_segment_engine(ctx)
        ctx.message_direction = run_message_direction_engine(ctx)

        apply_sleep_segment_intelligence(ctx)

        run_commercial_pre_engine(ctx)
        run_recommendation_engine(ctx)
        run_commercial_post_engine(ctx)
        run_forecast_engine(ctx)
        apply_calculation_framework(ctx)

    except Exception as exc:
        ctx.errors.append(str(exc))

    return ctx


def run_segmentation(customer: dict, datalogix: dict, zip_ref: dict | None) -> dict:
    raw = {
        "net_worth": datalogix.get("net_worth_indicator"),
        "online_access": datalogix.get("online_access_code"),
        "retail_card": datalogix.get("retail_card_code"),
        "home_value": datalogix.get("home_value_code"),
        "estimated_income": datalogix.get("estimated_income_code"),
        "generation": datalogix.get("generation"),
        "age_range": datalogix.get("age_range"),
        "length_of_residence": datalogix.get("length_of_residence"),
        "adults": datalogix.get("adults_in_household"),
        "children": datalogix.get("children_in_household"),
    }
    ctx = run_intelligence_pipeline(customer=customer, datalogix_raw=raw, zip_ref=zip_ref)
    return ctx.to_intelligence_dict()
