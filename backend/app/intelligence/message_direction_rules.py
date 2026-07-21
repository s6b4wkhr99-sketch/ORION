"""Message Direction Rule Library — Rules 041–048 (Volume 04 Section 14)."""

from dataclasses import dataclass
from typing import Callable

MESSAGE_DIRECTIONS = [
    "Premium Wellness Lifestyle Message",
    "Chronic Pain Relief Message",
    "Family Daily Wellness Message",
    "Affordable Wellness Routine Message",
    "Pain Relief + Value Message",
    "FDA Cleared Technology Trust Message",
    "Product Education Message",
    "Financing / Consultation CTA Message",
]

FAMILY_PRIZM = {"Kids and Cul-de-Sacs", "Caregiving Households"}


@dataclass
class MessageInputs:
    ceragem_segment: str
    prizm_segment: str
    purchase_power: float
    pain_index: float
    brand_familiarity_index: float
    family_messaging_hints: list[str]


def build_message_inputs(ctx) -> MessageInputs:
    intermediate = ctx.datalogix_intermediate or {}
    zip_intel = ctx.zip_intelligence or {}

    pp = ctx.purchase_power_index
    if not pp:
        pp = min(1.0, intermediate.get("purchase_readiness", 0.0) * 0.6 + zip_intel.get("geographic_purchasing_context", 0.0) * 0.4)

    pain = ctx.pain_index
    if not pain:
        pain = max(
            intermediate.get("generation_pain_tendency", 0.35),
            intermediate.get("age_life_stage_score", 0.35) * 0.5,
        )

    brand = ctx.brand_familiarity_index
    if not brand:
        brand = intermediate.get("brand_familiarity_signal", 0.0)

    return MessageInputs(
        ceragem_segment=ctx.ceragem_segment or "Mid-Low+ · Wellness",
        prizm_segment=ctx.prizm_proxy_segment or "Unknown",
        purchase_power=pp,
        pain_index=pain,
        brand_familiarity_index=brand,
        family_messaging_hints=intermediate.get("family_messaging_hints") or [],
    )


def rule_041_premium_wellness(inputs: MessageInputs) -> tuple[str | None, bool]:
    """Rule-041: Premium lifestyle wellness positioning — High + Wellness."""
    if inputs.ceragem_segment == "High + Wellness":
        return "Premium Wellness Lifestyle Message", True
    return None, False


def rule_042_chronic_pain_relief(inputs: MessageInputs) -> tuple[str | None, bool]:
    """Rule-042: Therapeutic relief — High + Pain Index, Mid-High + Pain Index."""
    if inputs.ceragem_segment in {"High + Pain Index", "Mid-High + Pain Index"}:
        return "Chronic Pain Relief Message", True
    return None, False


def rule_043_family_daily_wellness(inputs: MessageInputs) -> tuple[str | None, bool]:
    """Rule-043: Everyday family wellness."""
    if "family-oriented messaging" in inputs.family_messaging_hints:
        return "Family Daily Wellness Message", True
    if inputs.prizm_segment in FAMILY_PRIZM:
        return "Family Daily Wellness Message", True
    if "caregiving scenarios" in inputs.family_messaging_hints:
        return "Family Daily Wellness Message", True
    return None, False


def rule_044_affordable_wellness(inputs: MessageInputs) -> tuple[str | None, bool]:
    """Rule-044: Wellness without premium positioning — Mid-Low + Wellness."""
    if inputs.ceragem_segment == "Mid-Low + Wellness":
        return "Affordable Wellness Routine Message", True
    return None, False


def rule_045_pain_relief_value(inputs: MessageInputs) -> tuple[str | None, bool]:
    """Rule-045: Therapeutic messaging with affordability — Mid-Low + Pain Index."""
    if inputs.ceragem_segment == "Mid-Low + Pain Index":
        return "Pain Relief + Value Message", True
    return None, False


def rule_046_fda_trust(inputs: MessageInputs) -> tuple[str | None, bool]:
    """Rule-046: FDA Class 2 V-series trust — key purchase driver vs. commodity massage chairs."""
    if "Pain Index" in inputs.ceragem_segment:
        return "FDA Cleared Technology Trust Message", True
    if inputs.pain_index >= 0.35:
        return "FDA Cleared Technology Trust Message", True
    if inputs.brand_familiarity_index < 0.5 and inputs.purchase_power >= 0.35:
        return "FDA Cleared Technology Trust Message", True
    if inputs.prizm_segment in {"Wellness Seekers", "Suburban Sophisticates"} and inputs.brand_familiarity_index < 0.65:
        return "FDA Cleared Technology Trust Message", True
    return None, False


def rule_047_product_education(inputs: MessageInputs) -> tuple[str | None, bool]:
    """Rule-047: Product understanding for early-stage prospects."""
    if inputs.purchase_power < 0.4 and inputs.pain_index < 0.5:
        return "Product Education Message", True
    if inputs.ceragem_segment == "Mid-High + Wellness" and inputs.brand_familiarity_index < 0.5:
        return "Product Education Message", True
    return None, False


def rule_048_financing_consultation(inputs: MessageInputs) -> tuple[str | None, bool]:
    """Rule-048: Reduce purchase friction for price-sensitive customers."""
    if inputs.purchase_power < 0.5 and "Pain Index" not in inputs.ceragem_segment:
        return "Financing / Consultation CTA Message", True
    if inputs.ceragem_segment.startswith("Mid-Low") and inputs.purchase_power < 0.55:
        return "Financing / Consultation CTA Message", True
    return None, False


MESSAGE_RULE_CHAIN: list[tuple[str, str, Callable[[MessageInputs], tuple[str | None, bool]]]] = [
    ("Rule-041", "Premium Wellness Lifestyle Message Rule", rule_041_premium_wellness),
    ("Rule-042", "Chronic Pain Relief Message Rule", rule_042_chronic_pain_relief),
    ("Rule-043", "Family Daily Wellness Message Rule", rule_043_family_daily_wellness),
    ("Rule-044", "Affordable Wellness Routine Message Rule", rule_044_affordable_wellness),
    ("Rule-045", "Pain Relief + Value Message Rule", rule_045_pain_relief_value),
    ("Rule-046", "FDA Cleared Technology Trust Message Rule", rule_046_fda_trust),
    ("Rule-048", "Financing / Consultation CTA Message Rule", rule_048_financing_consultation),
    ("Rule-047", "Product Education Message Rule", rule_047_product_education),
]


def fallback_message_direction(inputs: MessageInputs) -> str:
    """Deterministic fallback — product education for unmatched profiles."""
    if "Pain Index" in inputs.ceragem_segment:
        return "Pain Relief + Value Message"
    if inputs.purchase_power >= 0.75:
        return "Premium Wellness Lifestyle Message"
    return "Product Education Message"
