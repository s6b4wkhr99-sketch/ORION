"""Message Direction Engine — Section 14 (Rules 041–048)."""

from app.intelligence.message_direction_rules import (
    MESSAGE_DIRECTIONS,
    MESSAGE_RULE_CHAIN,
    build_message_inputs,
    fallback_message_direction,
)
from app.intelligence.types import IntelligenceContext


def run_message_direction_engine(ctx: IntelligenceContext) -> str:
    """
    Section 14.4 workflow:
    Ceragem Segment → campaign objective rules → one primary Message Direction.
    """
    inputs = build_message_inputs(ctx)

    ctx.add_trace(
        "Rule-MD-001", "Single Message Direction Rule",
        {"ceragem_segment": inputs.ceragem_segment},
        {"one_direction_required": True},
        "One customer receives one primary Message Direction (Principle M-002).",
    )

    for rule_id, name, evaluator in MESSAGE_RULE_CHAIN:
        direction, matched = evaluator(inputs)
        ctx.add_trace(
            rule_id,
            name,
            {
                "ceragem_segment": inputs.ceragem_segment,
                "prizm_segment": inputs.prizm_segment,
                "purchase_power": inputs.purchase_power,
                "pain_index": inputs.pain_index,
            },
            {"matched": matched, "message_direction": direction},
            f"{name} evaluated from customer intelligence.",
        )
        if matched and direction in MESSAGE_DIRECTIONS:
            ctx.add_trace(
                "Rule-MD", "Message Direction Engine",
                {"matched_rule": rule_id},
                {"message_direction": direction},
                f"Message Direction assigned by {rule_id}.",
            )
            return direction

    direction = fallback_message_direction(inputs)
    ctx.add_trace(
        "Rule-MD", "Message Direction Engine",
        {"matched_rule": "fallback"},
        {"message_direction": direction},
        "Deterministic fallback after all message rules evaluated.",
    )
    return direction


def assign_message_direction(**kwargs) -> str:
    """Backward-compatible wrapper."""
    from app.intelligence.types import IntelligenceContext

    ctx = IntelligenceContext(
        prizm_proxy_segment=kwargs.get("prizm_segment"),
        ceragem_segment=kwargs.get("ceragem_segment"),
        purchase_power_index=kwargs.get("purchase_power", 0.0),
        pain_index=kwargs.get("pain_index", 0.0),
        datalogix_intermediate=kwargs.get("datalogix_intermediate") or {},
    )
    return run_message_direction_engine(ctx)
