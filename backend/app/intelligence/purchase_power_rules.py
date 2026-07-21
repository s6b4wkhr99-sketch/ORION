"""Purchase Power Rule Library — Rules 049–054 (Volume 04 Section 15)."""

from dataclasses import dataclass

from app.reference.registry import LEVEL_TO_INDEX, PURCHASE_POWER_LEVELS

PURCHASE_POWER_LEVELS = PURCHASE_POWER_LEVELS
LEVEL_TO_INDEX = LEVEL_TO_INDEX


@dataclass
class PurchasePowerInputs:
    premium_zip_indicator: bool
    median_income_context: float
    geographic_purchasing_context: float
    home_value_strength: float
    home_value_numeric: float | None
    income_numeric: float | None
    income_categorical_strength: float
    net_worth_strength: float
    residential_stability: float
    dwelling_type: str | None
    brand_familiarity_signal: float
    digital_engagement: float
    family_structure_score: float
    zip_income_tier: str = "Unknown"
    zip_purchase_potential: float = 0.0
    zip_income_baseline: bool = False


def build_purchase_power_inputs(ctx) -> PurchasePowerInputs:
    zip_intel = ctx.zip_intelligence or {}
    intermediate = ctx.datalogix_intermediate or {}

    income_numeric = intermediate.get("estimated_income_numeric")
    income_cat = intermediate.get("estimated_income_categorical")
    income_cat_strength = 0.0
    if income_numeric is None and income_cat:
        from app.intelligence.datalogix import income_signal_strength

        income_cat_strength = income_signal_strength(str(income_cat))

    zip_income_baseline = intermediate.get("estimated_income_source") == "zip_median_baseline"

    return PurchasePowerInputs(
        premium_zip_indicator=bool(zip_intel.get("premium_zip_indicator")),
        median_income_context=zip_intel.get("median_income_context", 0.0),
        geographic_purchasing_context=zip_intel.get("geographic_purchasing_context", 0.0),
        home_value_strength=intermediate.get("home_value_strength", 0.0),
        home_value_numeric=intermediate.get("home_value_numeric"),
        income_numeric=income_numeric,
        income_categorical_strength=income_cat_strength,
        net_worth_strength=intermediate.get("net_worth_strength", 0.0),
        residential_stability=intermediate.get("residential_stability", 0.0),
        dwelling_type=ctx.datalogix_signals.get("dwelling_type") or ctx.datalogix_raw.get("dwelling"),
        brand_familiarity_signal=intermediate.get("brand_familiarity_signal", 0.0),
        digital_engagement=intermediate.get("digital_engagement", 0.0),
        family_structure_score=intermediate.get("family_structure", 0.0),
        zip_income_tier=str(zip_intel.get("income_tier") or "Unknown"),
        zip_purchase_potential=float(zip_intel.get("purchase_potential_score") or 0.0),
        zip_income_baseline=zip_income_baseline,
    )


def rule_049_premium_geographic(inputs: PurchasePowerInputs) -> dict:
    """Rule-049: Top 50 ZIP and high median income increase confidence (supporting only)."""
    boost = 0.0
    if inputs.premium_zip_indicator:
        boost += 0.35
    if inputs.median_income_context >= 0.6:
        boost += 0.25
    boost += inputs.geographic_purchasing_context * 0.4
    return {
        "premium_zip_indicator": inputs.premium_zip_indicator,
        "median_income_context": inputs.median_income_context,
        "geographic_contribution": round(min(1.0, boost), 4),
        "supporting_only": True,
    }


def rule_050_home_value(inputs: PurchasePowerInputs) -> dict:
    """Rule-050: Home value increases confidence; no inference when unavailable."""
    if inputs.home_value_numeric is not None:
        contribution = min(1.0, inputs.home_value_numeric / 1_000_000)
    elif inputs.home_value_strength > 0:
        contribution = inputs.home_value_strength
    else:
        contribution = 0.0
    return {
        "home_value_numeric": inputs.home_value_numeric,
        "home_value_strength": inputs.home_value_strength,
        "contribution": round(contribution, 4),
    }


def rule_051_estimated_income(inputs: PurchasePowerInputs) -> dict:
    """Rule-051: Numeric income direct; categorical via interpretation only."""
    if inputs.income_numeric is not None:
        contribution = min(1.0, float(inputs.income_numeric) / 150_000)
        return {"format": "numeric", "contribution": round(contribution, 4)}
    if inputs.income_categorical_strength > 0:
        return {
            "format": "categorical",
            "contribution": round(inputs.income_categorical_strength, 4),
        }
    return {"format": "missing", "contribution": 0.0}


def rule_052_net_worth(inputs: PurchasePowerInputs) -> dict:
    """Rule-052: Net worth supports PP only; not Ceragem Segment directly."""
    return {
        "net_worth_strength": inputs.net_worth_strength,
        "contribution": round(inputs.net_worth_strength, 4),
    }


def rule_053_residential_stability(inputs: PurchasePowerInputs) -> dict:
    """Rule-053: Length of residence and dwelling type support PP."""
    dwelling_boost = 0.1 if inputs.dwelling_type and str(inputs.dwelling_type).strip() else 0.0
    contribution = min(1.0, inputs.residential_stability + dwelling_boost)
    return {
        "residential_stability": inputs.residential_stability,
        "dwelling_type": inputs.dwelling_type,
        "contribution": round(contribution, 4),
    }


def rule_054_composite_purchase_power(components: dict, inputs: PurchasePowerInputs | None = None) -> dict:
    """
    Rule-054: Composite evaluation in priority order.
    Weights reflect Section 15.4 priority list.
    ZIP median baseline (unitedstateszipcodes.org / ACS B19013) blends when Datalogix income is absent.
    """
    score = (
        components["geographic"]["geographic_contribution"] * 0.20
        + components["income"]["contribution"] * 0.20
        + components["home_value"]["contribution"] * 0.15
        + components["net_worth"]["contribution"] * 0.15
        + components["residence"]["contribution"] * 0.12
        + components["brand"]["contribution"] * 0.10
        + components["email"]["contribution"] * 0.08
    )

    if inputs and inputs.zip_purchase_potential > 0:
        if inputs.zip_income_baseline or components["income"].get("format") == "missing":
            score = score * 0.65 + inputs.zip_purchase_potential * 0.35
        elif inputs.zip_income_tier == "High":
            score = score * 0.85 + inputs.zip_purchase_potential * 0.15

    score = round(min(1.0, score), 4)

    if score >= 0.65:
        level = "High"
    elif score >= 0.35:
        level = "Medium"
    else:
        level = "Low"

    return {
        "composite_score": score,
        "purchase_power": level,
        "purchase_power_index": LEVEL_TO_INDEX[level],
    }


def evaluate_purchase_power(inputs: PurchasePowerInputs) -> tuple[dict, dict]:
    """Run Rules 049–054 and return component traces plus composite output."""
    geographic = rule_049_premium_geographic(inputs)
    home_value = rule_050_home_value(inputs)
    income = rule_051_estimated_income(inputs)
    net_worth = rule_052_net_worth(inputs)
    residence = rule_053_residential_stability(inputs)
    brand = {"contribution": round(inputs.brand_familiarity_signal, 4)}
    email = {"contribution": round(inputs.digital_engagement, 4)}

    components = {
        "geographic": geographic,
        "home_value": home_value,
        "income": income,
        "net_worth": net_worth,
        "residence": residence,
        "brand": brand,
        "email": email,
    }
    composite = rule_054_composite_purchase_power(components, inputs)
    return components, composite
