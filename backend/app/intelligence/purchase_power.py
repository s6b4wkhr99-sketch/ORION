"""Purchase Power Engine — Section 15 (Rules 049–054)."""

from app.intelligence.purchase_power_rules import build_purchase_power_inputs, evaluate_purchase_power
from app.intelligence.types import IntelligenceContext


def run_purchase_power_engine(ctx: IntelligenceContext) -> None:
    """
    Section 15.5 workflow:
    ZIP → income → residence → net worth → composite → High/Medium/Low.
    """
    inputs = build_purchase_power_inputs(ctx)
    components, composite = evaluate_purchase_power(inputs)

    ctx.add_trace(
        "Rule-049", "Premium Geographic Rule",
        {
            "premium_zip_indicator": inputs.premium_zip_indicator,
            "median_income_context": inputs.median_income_context,
        },
        components["geographic"],
        "Premium ZIP and median income increase purchasing confidence (supporting only).",
    )
    ctx.add_trace(
        "Rule-050", "Home Value Rule",
        {"home_value_strength": inputs.home_value_strength},
        components["home_value"],
        "Home value contributes when available; no inferred value when missing.",
    )
    ctx.add_trace(
        "Rule-051", "Estimated Income Rule",
        {"income_numeric": inputs.income_numeric},
        components["income"],
        "Numeric income direct; categorical codes via interpretation only.",
    )
    ctx.add_trace(
        "Rule-052", "Net Worth Rule",
        {"net_worth_strength": inputs.net_worth_strength},
        components["net_worth"],
        "Net worth supports Purchase Power only.",
    )
    ctx.add_trace(
        "Rule-053", "Residential Stability Rule",
        {
            "residential_stability": inputs.residential_stability,
            "dwelling_type": inputs.dwelling_type,
        },
        components["residence"],
        "Residence duration and dwelling type support Purchase Power.",
    )
    ctx.add_trace(
        "Rule-054", "Composite Purchase Power Rule",
        {
            "brand_familiarity": components["brand"]["contribution"],
            "email_responsiveness": components["email"]["contribution"],
            "components": {k: v for k, v in components.items()},
        },
        composite,
        "One Purchase Power value (High/Medium/Low) from weighted composite.",
    )

    ctx.purchase_power_category = composite["purchase_power"]
    ctx.purchase_power_index = composite["purchase_power_index"]

    ctx.add_trace(
        "Rule-PP", "Purchase Power Engine",
        {"purchase_power": ctx.purchase_power_category},
        {"purchase_power_index": ctx.purchase_power_index},
        "Derived probability of realistic Ceragem product purchase.",
    )
