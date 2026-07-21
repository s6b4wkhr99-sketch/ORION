"""Lifestyle Engine — Section 17 (Rules 060–064)."""

from app.intelligence.datalogix import is_strong
from app.intelligence.lifestyle_rules import build_lifestyle_inputs, evaluate_lifestyle
from app.intelligence.types import IntelligenceContext


def run_lifestyle_engine(ctx: IntelligenceContext) -> None:
    """
    Section 17.5 workflow:
    PRIZM + ZIP + digital + household → composite Lifestyle Index (High/Medium/Low).
    Does not evaluate income or purchasing capability (Principle LS-002).
    """
    inputs = build_lifestyle_inputs(ctx)
    components, composite = evaluate_lifestyle(inputs)
    intermediate = ctx.datalogix_intermediate or {}
    dlx = ctx.datalogix_signals

    ctx.add_trace(
        "Rule-060", "Wellness Lifestyle Rule",
        {"prizm_segment": inputs.prizm_segment},
        components["wellness"],
        "Wellness behavior requires multiple supporting signals.",
    )
    ctx.add_trace(
        "Rule-061", "Digital Engagement Rule",
        {"digital_engagement": inputs.digital_engagement},
        components["digital"],
        "Digital accessibility supports Lifestyle; never determines alone.",
    )
    ctx.add_trace(
        "Rule-062", "Retail Familiarity Rule",
        {"retail_familiarity": inputs.retail_familiarity},
        components["retail"],
        "Retail familiarity is supporting intelligence only.",
    )
    ctx.add_trace(
        "Rule-063", "Household Stability Rule",
        {
            "residential_stability": inputs.residential_stability,
            "family_structure": inputs.family_structure_score,
        },
        components["household"],
        "Stable households support consistent wellness behavior.",
    )
    ctx.add_trace(
        "Rule-064", "Composite Lifestyle Rule",
        {"components": components},
        composite,
        "One Lifestyle Index (High/Medium/Low) from composite evaluation.",
    )

    ctx.lifestyle_category = composite["lifestyle_index"]
    ctx.lifestyle_index = composite["lifestyle_index_numeric"]

    digital = intermediate.get("digital_engagement", 0.0)
    brand = intermediate.get("brand_familiarity_signal", 0.0)
    zip_intel = ctx.zip_intelligence or {}
    digital_geo = float(zip_intel.get("digital_geo_boost") or 0.0)
    brand_geo = float(zip_intel.get("brand_geo_boost") or 0.0)

    ctx.email_response_index = round(
        min(1.0, digital * 0.55 + digital_geo * 0.35 + (0.2 if is_strong(dlx.get("online_access_code", "")) else 0)),
        4,
    )
    ctx.brand_familiarity_index = round(min(1.0, brand * 0.50 + brand_geo * 0.50), 4)

    ctx.add_trace(
        "Rule-LS", "Lifestyle Engine",
        {"lifestyle_index": ctx.lifestyle_category},
        {
            "lifestyle_index_numeric": ctx.lifestyle_index,
            "email_response_index": ctx.email_response_index,
            "brand_familiarity_index": ctx.brand_familiarity_index,
        },
        "Proactive wellness motivation; preference not purchasing ability.",
    )
