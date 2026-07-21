"""ZIP Intelligence Engine — Section 11 (Rules 018–024)."""

from collections.abc import Callable

from app.intelligence.types import IntelligenceContext
from app.intelligence.zip_rules import (
    compose_zip_intelligence,
    rule_018_validate_zip,
    rule_019_normalize_zip,
    rule_020_lookup_zip,
    rule_021_median_income,
    rule_022_top50_income_zip,
    rule_023_state_verification,
    rule_024_reference_integrity,
)


def run_zip_intelligence_engine(
    ctx: IntelligenceContext,
    zip_lookup: Callable[[str], dict | None] | None = None,
) -> None:
    """
    Section 11.4 workflow:
    Validate → Normalize → Lookup → Load Reference → Generate ZIP Intelligence.
    """
    raw_zip = ctx.customer.get("zip")
    normalized = rule_019_normalize_zip(raw_zip)
    if normalized and len(normalized) == 5:
        ctx.customer["zip"] = normalized

    validation = rule_018_validate_zip(raw_zip, normalized)
    ctx.add_trace(
        "Rule-018", "ZIP Validation Rule",
        {"raw_zip": raw_zip},
        validation,
        "Invalid ZIPs stored; intelligence generated only when valid.",
    )
    ctx.add_trace(
        "Rule-019", "ZIP Normalization Rule",
        {"raw_zip": raw_zip},
        {"normalized_zip": normalized},
        "ZIP+4 extensions removed; five-digit ZIP used for lookup.",
    )

    reference_row: dict | None = None
    if validation["valid"] and normalized and zip_lookup:
        reference_row = zip_lookup(normalized)
    elif validation["valid"] and normalized and ctx.zip_ref:
        reference_row = ctx.zip_ref

    lookup = rule_020_lookup_zip(normalized or "", reference_row)
    ctx.add_trace(
        "Rule-020", "ZIP Intelligence Lookup Rule",
        {"lookup_key": normalized},
        lookup,
        "Reference data loaded from zip_intelligence when available.",
    )

    median = rule_021_median_income(lookup)
    ctx.add_trace(
        "Rule-021", "Median Income Rule",
        {"median_income": lookup.get("median_income")},
        median,
        "Median income supports Purchase Power and Revenue Forecast only.",
    )

    top50 = rule_022_top50_income_zip(lookup)
    ctx.add_trace(
        "Rule-022", "Top 50 Income ZIP Rule",
        {"top_50_income_rank": lookup.get("top_50_income_rank")},
        top50,
        "Premium ZIP status supports PRIZM, Purchase Power, and Recommendation.",
    )

    state_check = rule_023_state_verification(ctx.customer.get("state"), lookup.get("state"))
    ctx.add_trace(
        "Rule-023", "State Verification Rule",
        {"customer_state": ctx.customer.get("state"), "reference_state": lookup.get("state")},
        state_check,
        "Customer state never auto-corrected; mismatches logged.",
    )
    if state_check.get("mismatch"):
        ctx.errors.append(
            f"Rule-023 state_zip_mismatch: customer={state_check['customer_state']} "
            f"reference={state_check['reference_state']}"
        )

    integrity = rule_024_reference_integrity()
    ctx.add_trace(
        "Rule-024", "Reference Database Integrity Rule",
        {"database": "zip_intelligence"},
        integrity,
        "ZIP reference database is read-only during processing.",
    )

    ctx.zip_intelligence = compose_zip_intelligence(
        validation=validation,
        lookup=lookup,
        median=median,
        top50=top50,
        state_check=state_check,
    )
    ctx.zip_ref = lookup if lookup.get("found") else None

    ctx.add_trace(
        "Rule-ZI", "ZIP Intelligence Engine",
        {"zip": normalized},
        ctx.zip_intelligence,
        "Geographic intelligence generated for downstream engines.",
    )
