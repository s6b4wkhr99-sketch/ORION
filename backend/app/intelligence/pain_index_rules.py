"""Pain Index Rule Library — Rules 055–059 (Volume 04 Section 16)."""

from dataclasses import dataclass

from app.reference.registry import PAIN_INDEX_LEVELS as _PAIN_INDEX_SEED

PAIN_INDEX_LEVELS = tuple(level[0] for level in _PAIN_INDEX_SEED)
LEVEL_TO_INDEX = {level[0]: level[3] for level in _PAIN_INDEX_SEED}

PAIN_PRIZM = {"Aging in Place", "Caregiving Households", "Simple Life"}


@dataclass
class PainIndexInputs:
    age_life_stage_score: float
    generation_pain_tendency: float
    residential_stability: float
    dwelling_type: str | None
    family_structure_score: float
    family_messaging_hints: list[str]
    lifestyle_signals: float
    wellness_signals: float
    prizm_segment: str
    purchase_power: str
    purchase_power_index: float
    pain_geo_boost: float = 0.0


def build_pain_index_inputs(ctx) -> PainIndexInputs:
    intermediate = ctx.datalogix_intermediate or {}
    zip_intel = ctx.zip_intelligence or {}
    return PainIndexInputs(
        age_life_stage_score=intermediate.get("age_life_stage_score", 0.35),
        generation_pain_tendency=intermediate.get("generation_pain_tendency", 0.35),
        residential_stability=intermediate.get("residential_stability", 0.0),
        dwelling_type=ctx.datalogix_signals.get("dwelling_type") or ctx.datalogix_raw.get("dwelling"),
        family_structure_score=intermediate.get("family_structure", 0.0),
        family_messaging_hints=intermediate.get("family_messaging_hints") or [],
        lifestyle_signals=intermediate.get("lifestyle_signals", 0.0),
        wellness_signals=intermediate.get("wellness_signals", 0.0),
        prizm_segment=ctx.prizm_proxy_segment or "Unknown",
        purchase_power=ctx.purchase_power_category or "Low",
        purchase_power_index=ctx.purchase_power_index,
        pain_geo_boost=float(zip_intel.get("pain_geo_boost") or 0.0),
    )


def rule_055_age_influence(inputs: PainIndexInputs) -> dict:
    """Rule-055: Age supports pain index; never alone."""
    return {
        "age_life_stage_score": inputs.age_life_stage_score,
        "contribution": round(inputs.age_life_stage_score * 0.5, 4),
        "supporting_only": True,
    }


def rule_056_generation(inputs: PainIndexInputs) -> dict:
    """Rule-056: Generation supports pain index together with age."""
    return {
        "generation_pain_tendency": inputs.generation_pain_tendency,
        "contribution": round(inputs.generation_pain_tendency * 0.5, 4),
    }


def rule_057_residence_stability(inputs: PainIndexInputs) -> dict:
    """Rule-057: Long residence supports mature household; alone does not increase pain."""
    if inputs.residential_stability < 0.5:
        contribution = inputs.residential_stability * 0.2
    else:
        contribution = min(0.35, inputs.residential_stability * 0.3)
    return {
        "residential_stability": inputs.residential_stability,
        "dwelling_type": inputs.dwelling_type,
        "contribution": round(contribution, 4),
        "supporting_only": True,
    }


def rule_058_lifestyle_interaction(inputs: PainIndexInputs) -> dict:
    """Rule-058: Strong wellness/lifestyle lowers therapeutic emphasis."""
    moderation = min(0.4, inputs.lifestyle_signals * 0.25 + inputs.wellness_signals * 0.15)
    return {
        "lifestyle_signals": inputs.lifestyle_signals,
        "wellness_signals": inputs.wellness_signals,
        "pain_moderation": round(moderation, 4),
    }


def rule_059_composite_pain_index(components: dict, inputs: PainIndexInputs) -> dict:
    """Rule-059: Composite age, generation, lifestyle, residence, household."""
    raw = (
        components["age"]["contribution"]
        + components["generation"]["contribution"]
        + components["residence"]["contribution"]
        + min(0.2, inputs.family_structure_score * 0.15)
    )
    if inputs.prizm_segment in PAIN_PRIZM:
        raw += 0.1
    if "caregiving scenarios" in inputs.family_messaging_hints:
        raw += 0.05

    raw -= components["lifestyle"]["pain_moderation"]
    raw += inputs.pain_geo_boost
    score = round(max(0.0, min(1.0, raw)), 4)

    if score >= 0.6:
        level = "High"
    elif score >= 0.35:
        level = "Medium"
    else:
        level = "Low"

    return {
        "composite_score": score,
        "pain_index": level,
        "pain_index_numeric": LEVEL_TO_INDEX[level],
    }


def evaluate_pain_index(inputs: PainIndexInputs) -> tuple[dict, dict]:
    """Run Rules 055–059."""
    age = rule_055_age_influence(inputs)
    generation = rule_056_generation(inputs)
    residence = rule_057_residence_stability(inputs)
    lifestyle = rule_058_lifestyle_interaction(inputs)
    components = {"age": age, "generation": generation, "residence": residence, "lifestyle": lifestyle}
    composite = rule_059_composite_pain_index(components, inputs)
    return components, composite
