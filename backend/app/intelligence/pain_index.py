"""Pain Index Engine — Section 16 (Rules 055–059)."""

from app.intelligence.pain_index_rules import build_pain_index_inputs, evaluate_pain_index
from app.intelligence.types import IntelligenceContext


def run_pain_index_engine(ctx: IntelligenceContext) -> None:
    """
    Section 16.5 workflow:
    Age → lifestyle moderation → residence → household → composite → High/Medium/Low.
    """
    inputs = build_pain_index_inputs(ctx)
    components, composite = evaluate_pain_index(inputs)

    ctx.add_trace(
        "Rule-055", "Age Influence Rule",
        {"age_life_stage_score": inputs.age_life_stage_score},
        components["age"],
        "Age supports Pain Index; never determines alone.",
    )
    ctx.add_trace(
        "Rule-056", "Generation Rule",
        {"generation_pain_tendency": inputs.generation_pain_tendency},
        components["generation"],
        "Generation supports Pain Index together with Age Range.",
    )
    ctx.add_trace(
        "Rule-057", "Residence Stability Rule",
        {"residential_stability": inputs.residential_stability},
        components["residence"],
        "Long residence supports mature household context only.",
    )
    ctx.add_trace(
        "Rule-058", "Lifestyle Interaction Rule",
        {
            "lifestyle_signals": inputs.lifestyle_signals,
            "wellness_signals": inputs.wellness_signals,
        },
        components["lifestyle"],
        "Strong wellness characteristics lower therapeutic emphasis.",
    )
    ctx.add_trace(
        "Rule-059", "Composite Pain Index Rule",
        {
            "prizm_segment": inputs.prizm_segment,
            "purchase_power": inputs.purchase_power,
            "family_structure": inputs.family_structure_score,
        },
        composite,
        "One Pain Index value (High/Medium/Low) from composite evaluation.",
    )

    ctx.pain_index_category = composite["pain_index"]
    ctx.pain_index = composite["pain_index_numeric"]

    ctx.add_trace(
        "Rule-PI", "Pain Index Engine",
        {"pain_index": ctx.pain_index_category},
        {"pain_index_numeric": ctx.pain_index},
        "Commercial therapeutic motivation indicator; not a medical diagnosis.",
    )
