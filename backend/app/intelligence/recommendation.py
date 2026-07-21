"""Recommendation Engine — Section 18 (Rules 065–067)."""

from app.intelligence.recommendation_rationale import build_recommendation_rationale
from app.intelligence.recommendation_rules import build_recommendation_inputs, evaluate_recommendation
from app.intelligence.types import IntelligenceContext


def run_recommendation_engine(ctx: IntelligenceContext) -> None:
    """
    Section 18.5 workflow:
    Ceragem + Lifestyle + Pain + PP → product, strategy, priority.
    """
    inputs = build_recommendation_inputs(ctx)
    result = evaluate_recommendation(inputs)

    ctx.add_trace(
        "Rule-065", "Product Recommendation Rule",
        {
            "ceragem_segment": inputs.ceragem_segment,
            "purchase_power": inputs.purchase_power_category,
            "lifestyle": inputs.lifestyle_category,
            "pain_index": inputs.pain_index_category,
        },
        result["product"],
        "Exactly one primary product recommendation.",
    )
    ctx.add_trace(
        "Rule-066", "Campaign Priority Rule",
        {
            "purchase_power": inputs.purchase_power_category,
            "lifestyle": inputs.lifestyle_category,
            "pain_index": inputs.pain_index_category,
            "email_responsiveness": inputs.email_response_index,
        },
        result["priority"],
        "One Campaign Priority (High/Medium/Low) per customer.",
    )
    ctx.add_trace(
        "Rule-067", "Campaign Strategy Rule",
        {"ceragem_segment": inputs.ceragem_segment},
        result["strategy"],
        "One campaign strategy follows Ceragem Segment.",
    )

    ctx.recommended_product = result["product"]["recommended_product"]
    ctx.campaign_priority_category = result["priority"]["campaign_priority"]
    ctx.campaign_priority = result["priority"]["campaign_priority_score"]
    ctx.campaign_strategy = result["strategy"]["campaign_strategy"]

    rationale = build_recommendation_rationale(ctx, result)
    ctx.recommendation_rationale = rationale
    ctx.add_trace(
        "Rule-REC-RATIONALE",
        "Product Recommendation Rationale",
        {
            "ceragem_segment": inputs.ceragem_segment,
            "purchase_power": inputs.purchase_power_category,
            "pain_index": inputs.pain_index_category,
            "lifestyle": inputs.lifestyle_category,
            "sleep_segment": inputs.sleep_segment,
        },
        rationale,
        rationale.get("summary") or "Product recommendation rationale generated.",
    )

    ctx.add_trace(
        "Rule-RC", "Recommendation Engine",
        {
            "recommended_product": ctx.recommended_product,
            "campaign_strategy": ctx.campaign_strategy,
            "campaign_priority": ctx.campaign_priority_category,
        },
        {"communication_strategy": result["strategy"]["communication_strategy"]},
        "Deterministic business recommendations with full rule traceability.",
    )
