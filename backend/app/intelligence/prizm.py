"""PRIZM Proxy Engine — Section 12 (Rules 025–033)."""

from app.intelligence.prizm_rules import PRIZM_RULE_CHAIN, PRIZM_SEGMENTS, build_prizm_inputs
from app.intelligence.types import IntelligenceContext

UNKNOWN = "Unknown"


def run_prizm_proxy_engine(ctx: IntelligenceContext) -> str:
    """
    Section 12.4 workflow:
    Evaluate all rules in order; assign exactly one segment (Rule-025); Unknown last (Rule-026).
    """
    inputs = build_prizm_inputs(ctx)

    ctx.add_trace(
        "Rule-025", "Single Segment Rule",
        {"approved_sources": ["ZIP Intelligence", "Datalogix Intelligence", "Household", "Residence"]},
        {"single_segment_required": True},
        "Every customer receives one and only one PRIZM Proxy Segment.",
    )

    for rule_id, name, evaluator in PRIZM_RULE_CHAIN:
        segment, matched = evaluator(inputs)
        ctx.add_trace(
            rule_id,
            name,
            {
                "geographic_context": inputs.geographic_purchasing_context,
                "premium_zip": inputs.premium_zip_indicator,
                "purchase_readiness": inputs.purchase_readiness,
                "residential_stability": inputs.residential_stability,
            },
            {"matched": matched, "segment": segment},
            f"{name} evaluated.",
        )
        if matched and segment in PRIZM_SEGMENTS:
            return segment

    ctx.add_trace(
        "Rule-026", "Unknown Minimization Rule",
        {"rules_evaluated": len(PRIZM_RULE_CHAIN)},
        {"segment": UNKNOWN},
        "All supported rules evaluated; Unknown assigned as final fallback.",
    )
    return UNKNOWN


def assign_prizm_proxy(**kwargs) -> str:
    """Backward-compatible wrapper — prefer run_prizm_proxy_engine on IntelligenceContext."""
    from app.intelligence.types import IntelligenceContext

    ctx = IntelligenceContext(
        customer={"state": kwargs.get("state"), "zip": kwargs.get("zip_code")},
        zip_ref=kwargs.get("zip_ref"),
        datalogix_signals=kwargs.get("datalogix") or {},
    )
    if ctx.zip_ref:
        ctx.zip_intelligence = {
            "available": True,
            "geographic_purchasing_context": 0.5 if ctx.zip_ref.get("top_50_income_rank") else 0.3,
            "premium_zip_indicator": bool(ctx.zip_ref.get("top_50_income_rank")),
            "median_income": ctx.zip_ref.get("median_income"),
        }
    ctx.datalogix_intermediate = (kwargs.get("datalogix") or {}).get("intermediate") or {}
    return run_prizm_proxy_engine(ctx)
