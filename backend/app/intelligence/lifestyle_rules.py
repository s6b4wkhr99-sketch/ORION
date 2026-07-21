"""Lifestyle Rule Library — Rules 060–064 (Volume 04 Section 17)."""

from dataclasses import dataclass

from app.reference.registry import LIFESTYLE_LEVELS as _LIFESTYLE_SEED

LIFESTYLE_LEVELS = tuple(level[0] for level in _LIFESTYLE_SEED)
LEVEL_TO_INDEX = {level[0]: level[2] for level in _LIFESTYLE_SEED}

WELLNESS_PRIZM = {"Established Elite", "Suburban Sophisticates", "Wellness Seekers", "Booming with Confidence"}


@dataclass
class LifestyleInputs:
    prizm_segment: str
    geographic_context: float
    premium_zip: bool
    digital_engagement: float
    retail_familiarity: float
    residential_stability: float
    family_structure_score: float
    purchase_power_category: str
    pain_index_category: str


def build_lifestyle_inputs(ctx) -> LifestyleInputs:
    intermediate = ctx.datalogix_intermediate or {}
    zip_intel = ctx.zip_intelligence or {}
    from app.intelligence.datalogix import signal_strength

    retail = signal_strength(ctx.datalogix_signals.get("retail_card_code", ""))

    return LifestyleInputs(
        prizm_segment=ctx.prizm_proxy_segment or "Unknown",
        geographic_context=zip_intel.get("geographic_purchasing_context", 0.0),
        premium_zip=bool(zip_intel.get("premium_zip_indicator")),
        digital_engagement=intermediate.get("digital_engagement", 0.0),
        retail_familiarity=retail,
        residential_stability=intermediate.get("residential_stability", 0.0),
        family_structure_score=intermediate.get("family_structure", 0.0),
        purchase_power_category=ctx.purchase_power_category or "Low",
        pain_index_category=ctx.pain_index_category or "Low",
    )


def rule_060_wellness_lifestyle(inputs: LifestyleInputs) -> dict:
    """Rule-060: Wellness PRIZM + digital engagement + stable household."""
    wellness_prizm = inputs.prizm_segment in WELLNESS_PRIZM
    digital = inputs.digital_engagement >= 0.5
    stable = inputs.residential_stability >= 0.5 or inputs.family_structure_score >= 0.3
    signals = sum([wellness_prizm, digital, stable])
    contribution = round(min(1.0, signals * 0.25), 4) if signals >= 2 else round(signals * 0.1, 4)
    return {
        "wellness_prizm": wellness_prizm,
        "digital_engagement": inputs.digital_engagement,
        "stable_household": stable,
        "contribution": contribution,
    }


def rule_061_digital_engagement(inputs: LifestyleInputs) -> dict:
    """Rule-061: Online access — supporting only, never alone."""
    return {
        "digital_engagement": inputs.digital_engagement,
        "contribution": round(inputs.digital_engagement * 0.35, 4),
        "supporting_only": True,
    }


def rule_062_retail_familiarity(inputs: LifestyleInputs) -> dict:
    """Rule-062: Retail card familiarity — supporting only."""
    return {
        "retail_familiarity": inputs.retail_familiarity,
        "contribution": round(inputs.retail_familiarity * 0.25, 4),
        "supporting_only": True,
    }


def rule_063_household_stability(inputs: LifestyleInputs) -> dict:
    """Rule-063: Household composition + residence stability."""
    contribution = min(
        1.0,
        inputs.residential_stability * 0.2 + inputs.family_structure_score * 0.15,
    )
    return {
        "residential_stability": inputs.residential_stability,
        "family_structure_score": inputs.family_structure_score,
        "contribution": round(contribution, 4),
    }


def rule_064_composite_lifestyle(components: dict, inputs: LifestyleInputs) -> dict:
    """Rule-064: Composite → High / Medium / Low."""
    score = (
        components["wellness"]["contribution"]
        + components["digital"]["contribution"]
        + components["retail"]["contribution"]
        + components["household"]["contribution"]
        + inputs.geographic_context * 0.15
        + (0.1 if inputs.prizm_segment in WELLNESS_PRIZM else 0.0)
    )
    if inputs.pain_index_category == "High":
        score *= 0.85
    score = round(min(1.0, score), 4)

    if score >= 0.6:
        level = "High"
    elif score >= 0.35:
        level = "Medium"
    else:
        level = "Low"

    return {
        "composite_score": score,
        "lifestyle_index": level,
        "lifestyle_index_numeric": LEVEL_TO_INDEX[level],
    }


def evaluate_lifestyle(inputs: LifestyleInputs) -> tuple[dict, dict]:
    wellness = rule_060_wellness_lifestyle(inputs)
    digital = rule_061_digital_engagement(inputs)
    retail = rule_062_retail_familiarity(inputs)
    household = rule_063_household_stability(inputs)
    components = {"wellness": wellness, "digital": digital, "retail": retail, "household": household}
    composite = rule_064_composite_lifestyle(components, inputs)
    return components, composite
