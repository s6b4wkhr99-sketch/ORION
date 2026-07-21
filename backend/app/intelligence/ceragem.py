"""Ceragem Segment Engine — purchase-power tier + recommendation axis."""

from app.intelligence.ceragem_rules import assign_ceragem_segment_from_context, build_ceragem_inputs
from app.intelligence.types import IntelligenceContext


def run_ceragem_segment_engine(ctx: IntelligenceContext) -> str:
    """
    Assign Ceragem Segment after Purchase Power, Pain, and Lifestyle engines.

    Format: ``{tier} · {axis}`` e.g. ``High+ · Wellness``.
    Tier = baseline purchase power; axis = Pain / Wellness for product rules.
    """
    inputs = build_ceragem_inputs(ctx)

    ctx.add_trace(
        "Rule-034",
        "Ceragem Tier Assignment",
        {
            "purchase_power_index": inputs.purchase_power_index,
            "premium_zip": inputs.premium_zip_indicator,
            "geographic_purchasing_context": inputs.geographic_purchasing_context,
        },
        {"ceragem_tier": inputs.tier},
        "Purchase-power baseline tier (High+ … Low+).",
    )
    ctx.add_trace(
        "Rule-034b",
        "Ceragem Axis Assignment",
        {
            "pain_index": inputs.pain_index,
            "lifestyle_index": inputs.lifestyle_index,
            "prizm_segment": inputs.prizm_segment,
        },
        {"segment_axis": inputs.axis},
        "Pain / Wellness axis for product recommendation — separate from tier.",
    )
    ctx.add_trace(
        "Rule-CS",
        "Ceragem Segment Engine",
        {"ceragem_tier": inputs.tier, "segment_axis": inputs.axis},
        {"ceragem_segment": inputs.segment},
        "Composite segment = tier · axis.",
    )
    return inputs.segment


def assign_ceragem_segment(**kwargs) -> str:
    """Backward-compatible wrapper."""
    from app.intelligence.types import IntelligenceContext

    ctx = IntelligenceContext(
        prizm_proxy_segment=kwargs.get("prizm_segment"),
        purchase_power_index=kwargs.get("purchase_power", 0.0),
        pain_index=kwargs.get("pain_index", 0.0),
        lifestyle_index=kwargs.get("lifestyle_index", 0.0),
    )
    if kwargs.get("zip_intelligence"):
        ctx.zip_intelligence = kwargs["zip_intelligence"]
    return run_ceragem_segment_engine(ctx)
