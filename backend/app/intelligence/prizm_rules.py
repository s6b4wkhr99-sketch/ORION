"""PRIZM Proxy Rule Library — Rules 025–033 (Volume 04 Section 12)."""

from dataclasses import dataclass
from typing import Callable

from app.intelligence.datalogix import normalize_code, signal_strength
from app.reference.registry import PRIZM_SEGMENTS

PRIZM_SEGMENTS = [segment[0] for segment in PRIZM_SEGMENTS]


@dataclass
class PrizmInputs:
    state: str | None
    zip_code: str | None
    geographic_purchasing_context: float
    premium_zip_indicator: bool
    median_income: float
    residential_stability: float
    purchase_readiness: float
    lifestyle_signals: float
    wellness_signals: float
    digital_engagement: float
    family_structure_score: float
    family_messaging_hints: list[str]
    children_count: int
    adults_count: int
    persons_count: int
    generation: str
    net_worth_strength: float
    home_value_strength: float
    retail_card_strength: float


def build_prizm_inputs(ctx) -> PrizmInputs:
    zip_intel = ctx.zip_intelligence or {}
    dlx = ctx.datalogix_signals or {}
    intermediate = ctx.datalogix_intermediate or {}

    return PrizmInputs(
        state=ctx.customer.get("state"),
        zip_code=ctx.customer.get("zip"),
        geographic_purchasing_context=zip_intel.get("geographic_purchasing_context", 0.0),
        premium_zip_indicator=zip_intel.get("premium_zip_indicator", False),
        median_income=float(zip_intel.get("median_income") or intermediate.get("estimated_income_numeric") or 0),
        residential_stability=intermediate.get("residential_stability", 0.0),
        purchase_readiness=intermediate.get("purchase_readiness", 0.0),
        lifestyle_signals=intermediate.get("lifestyle_signals", 0.0),
        wellness_signals=intermediate.get("wellness_signals", 0.0),
        digital_engagement=intermediate.get("digital_engagement", 0.0),
        family_structure_score=intermediate.get("family_structure", 0.0),
        family_messaging_hints=intermediate.get("family_messaging_hints") or [],
        children_count=_count(dlx.get("children_in_household")),
        adults_count=_count(dlx.get("adults_in_household"), 1),
        persons_count=_count(dlx.get("persons_in_household")),
        generation=normalize_code(dlx.get("generation")),
        net_worth_strength=intermediate.get("net_worth_strength", 0.0),
        home_value_strength=intermediate.get("home_value_strength", 0.0),
        retail_card_strength=signal_strength(dlx.get("retail_card_code", "")),
    )


def rule_027_established_elite(inputs: PrizmInputs) -> tuple[str | None, bool]:
    """Rule-027: Multiple supporting indicators required — no single variable."""
    indicators = [
        inputs.geographic_purchasing_context >= 0.65,
        inputs.premium_zip_indicator,
        inputs.residential_stability >= 0.7,
        inputs.purchase_readiness >= 0.7,
        inputs.median_income >= 90000,
    ]
    if sum(indicators) >= 3:
        return "Established Elite", True
    return None, False


def rule_028_suburban_sophisticates(inputs: PrizmInputs) -> tuple[str | None, bool]:
    """Rule-028: Stable residence, family household, strong lifestyle."""
    if (
        inputs.residential_stability >= 0.7
        and inputs.children_count >= 1
        and inputs.lifestyle_signals >= 0.55
    ):
        return "Suburban Sophisticates", True
    if inputs.home_value_strength >= 0.7 and inputs.residential_stability >= 0.7 and inputs.children_count >= 1:
        return "Suburban Sophisticates", True
    return None, False


def rule_029_kids_and_cul_de_sacs(inputs: PrizmInputs) -> tuple[str | None, bool]:
    """Rule-029: Children present, family household, residential stability."""
    if inputs.children_count >= 1 and inputs.adults_count >= 2 and inputs.residential_stability >= 0.5:
        return "Kids and Cul-de-Sacs", True
    return None, False


def rule_030_wellness_seekers(inputs: PrizmInputs) -> tuple[str | None, bool]:
    """Rule-030: Wellness indicators, digital engagement, lifestyle signals."""
    if (
        inputs.wellness_signals >= 0.55
        and inputs.digital_engagement >= 0.7
        and inputs.lifestyle_signals >= 0.55
    ):
        return "Wellness Seekers", True
    if inputs.digital_engagement >= 0.5 and inputs.lifestyle_signals >= 0.5:
        return "Wellness Seekers", True
    return None, False


def rule_031_aging_in_place(inputs: PrizmInputs) -> tuple[str | None, bool]:
    """Rule-031: Mature household, long residence, wellness support."""
    mature = inputs.generation in {"BOOMER", "SILENT", "GREATEST", "MATURE"}
    if mature and inputs.residential_stability >= 0.7 and inputs.adults_count <= 2:
        return "Aging in Place", True
    if inputs.residential_stability >= 0.5 and mature:
        return "Aging in Place", True
    return None, False


def rule_032_caregiving_households(inputs: PrizmInputs) -> tuple[str | None, bool]:
    """Rule-032: Multi-person household with family support characteristics."""
    if inputs.persons_count >= 3 and inputs.adults_count >= 2:
        return "Caregiving Households", True
    if "caregiving scenarios" in inputs.family_messaging_hints and inputs.adults_count >= 2:
        return "Caregiving Households", True
    if inputs.children_count >= 1 and inputs.adults_count >= 2 and inputs.retail_card_strength >= 0.7:
        return "Caregiving Households", True
    return None, False


def rule_033_simple_life(inputs: PrizmInputs) -> tuple[str | None, bool]:
    """Rule-033: Modest geographic profile, lower purchasing context, stable household."""
    if (
        inputs.geographic_purchasing_context < 0.35
        and inputs.purchase_readiness < 0.45
        and inputs.residential_stability >= 0.35
    ):
        return "Simple Life", True
    if inputs.median_income < 45000 and inputs.home_value_strength <= 0.35:
        return "Simple Life", True
    return None, False


def rule_booming_with_confidence(inputs: PrizmInputs) -> tuple[str | None, bool]:
    """Supported segment — strong income and purchase context without premium ZIP elite profile."""
    if inputs.median_income >= 65000 and inputs.purchase_readiness >= 0.5:
        return "Booming with Confidence", True
    return None, False


PRIZM_RULE_CHAIN: list[tuple[str, str, Callable[[PrizmInputs], tuple[str | None, bool]]]] = [
    ("Rule-027", "Established Elite Rule", rule_027_established_elite),
    ("Rule-028", "Suburban Sophisticates Rule", rule_028_suburban_sophisticates),
    ("Rule-029", "Kids and Cul-de-Sacs Rule", rule_029_kids_and_cul_de_sacs),
    ("Rule-030", "Wellness Seekers Rule", rule_030_wellness_seekers),
    ("Rule-031", "Aging in Place Rule", rule_031_aging_in_place),
    ("Rule-032", "Caregiving Households Rule", rule_032_caregiving_households),
    ("Rule-BC", "Booming with Confidence Rule", rule_booming_with_confidence),
    ("Rule-033", "Simple Life Rule", rule_033_simple_life),
]


def _count(value, default=0) -> int:
    if value is None or str(value).strip() == "":
        return default
    try:
        return int(float(str(value)))
    except ValueError:
        return default
