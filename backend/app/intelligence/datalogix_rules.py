"""Datalogix Rule Library — Rules 007–017 (Volume 04 Section 10)."""

from app.intelligence.datalogix import (
    is_categorical_code,
    is_numeric_value,
    normalize_code,
    parse_numeric,
    signal_strength,
)

ONLINE_ACCESS_LABELS = {
    "X": "Very High Digital Accessibility",
    "Y": "High Digital Accessibility",
    "U": "Moderate Digital Accessibility",
    "Z": "Low Digital Accessibility",
}

GENERATION_MESSAGING_TONE = {
    "GENZ": "Trend-forward, digital-first tone",
    "MILLENNIAL": "Balanced wellness and convenience tone",
    "GENX": "Practical value and reliability tone",
    "BOOMER": "Trust, comfort, and proven-results tone",
    "SILENT": "Gentle, respectful wellness tone",
    "GREATEST": "Gentle, respectful wellness tone",
    "MATURE": "Gentle, respectful wellness tone",
}


def rule_007_online_access(raw: str | None) -> dict:
    """Rule-007: Online Access → Digital Engagement (Email Responsiveness input)."""
    code = normalize_code(raw)
    score = signal_strength(code)
    return {
        "raw": raw,
        "code": code,
        "digital_engagement": score,
        "label": ONLINE_ACCESS_LABELS.get(code, "Unknown Digital Accessibility"),
    }


def rule_008_retail_card(raw: str | None) -> dict:
    """Rule-008: Retail Card → Brand Familiarity only (not Purchase Power)."""
    code = normalize_code(raw)
    return {
        "raw": raw,
        "code": code,
        "brand_familiarity_contribution": signal_strength(code),
    }


def rule_009_net_worth(raw: str | None) -> dict:
    """Rule-009: Net Worth → Purchase Power only (not Ceragem Segment directly)."""
    code = normalize_code(raw)
    return {
        "raw": raw,
        "code": code,
        "purchase_power_contribution": signal_strength(code),
    }


def rule_010_length_of_residence(raw: str | None) -> dict:
    """Rule-010: Length of Residence → Residential Stability (supporting variable)."""
    code = normalize_code(raw)
    return {
        "raw": raw,
        "code": code,
        "residential_stability": signal_strength(code),
    }


def rule_011_household_composition(
    *,
    adults: str | None,
    children: str | None,
    persons: str | None,
    household: str | None,
) -> dict:
    """Rule-011: Household composition → family structure (supporting, not Ceragem direct)."""
    adult_count = _count(adults, default=0)
    child_count = _count(children, default=0)
    person_count = _count(persons, default=adult_count + child_count)

    hints: list[str] = []
    if child_count >= 1:
        hints.append("family-oriented messaging")
    if adult_count >= 2 and child_count >= 1:
        hints.append("caregiving scenarios")
    if person_count >= 2:
        hints.append("wellness messaging")

    household_text = (household or "").strip().lower()
    if "family" in household_text or "child" in household_text:
        if "family-oriented messaging" not in hints:
            hints.append("family-oriented messaging")
    if "single" in household_text or "solo" in household_text:
        hints.append("individual wellness messaging")

    structure_score = min(1.0, (adult_count * 0.15 + child_count * 0.25 + person_count * 0.1))

    return {
        "adults": adults,
        "children": children,
        "persons": persons,
        "household_composition": household,
        "family_structure_score": round(structure_score, 4),
        "messaging_hints": hints,
    }


def rule_012_estimated_income(raw: str | None) -> dict:
    """Rule-012: Estimated Income — numeric normalized; categorical preserved as-is."""
    if not raw or not str(raw).strip():
        return {"raw": raw, "format": "missing", "numeric_value": None, "categorical_code": None}

    text = str(raw).strip()
    if is_categorical_code(text):
        return {
            "raw": raw,
            "format": "categorical",
            "numeric_value": None,
            "categorical_code": text.upper(),
        }

    if is_numeric_value(text):
        numeric = parse_numeric(text)
        return {
            "raw": raw,
            "format": "numeric",
            "numeric_value": numeric,
            "categorical_code": None,
        }

    return {
        "raw": raw,
        "format": "categorical",
        "numeric_value": None,
        "categorical_code": normalize_code(text) or text,
    }


def rule_013_home_value(raw: str | None) -> dict:
    """Rule-013: Home Value — numeric contributes directly; categorical code preserved."""
    if not raw or not str(raw).strip():
        return {
            "raw": raw,
            "format": "missing",
            "numeric_value": None,
            "categorical_code": None,
            "purchase_power_contribution": 0.0,
        }

    text = str(raw).strip()
    if is_categorical_code(text):
        code = normalize_code(text)
        return {
            "raw": raw,
            "format": "categorical",
            "numeric_value": None,
            "categorical_code": code,
            "purchase_power_contribution": signal_strength(code),
        }

    if is_numeric_value(text):
        numeric = parse_numeric(text)
        contribution = min(1.0, (numeric or 0) / 1_000_000) if numeric else 0.0
        return {
            "raw": raw,
            "format": "numeric",
            "numeric_value": numeric,
            "categorical_code": None,
            "purchase_power_contribution": round(contribution, 4),
        }

    code = normalize_code(text)
    return {
        "raw": raw,
        "format": "categorical",
        "numeric_value": None,
        "categorical_code": code,
        "purchase_power_contribution": signal_strength(code),
    }


def rule_014_age_range(raw: str | None) -> dict:
    """Rule-014: Age Range → life stage (supporting: Lifestyle, Pain, Message Direction)."""
    text = (raw or "").strip()
    score = 0.35
    if text:
        prefix = text[0]
        if prefix in {"6", "7", "8", "9"}:
            score = 0.75
        elif prefix in {"4", "5"}:
            score = 0.55
        elif prefix in {"2", "3"}:
            score = 0.45
        elif prefix in {"1", "0"}:
            score = 0.35

    return {
        "raw": raw,
        "life_stage_score": round(score, 4),
        "life_stage_label": _age_label(text),
    }


def rule_015_generation(raw: str | None) -> dict:
    """Rule-015: Generation → lifestyle/pain/messaging tone (not revenue forecasting)."""
    code = normalize_code(raw)
    gen_key = code.replace(" ", "").replace("-", "").upper()
    tone = GENERATION_MESSAGING_TONE.get(gen_key, "General wellness tone")

    lifestyle_score = signal_strength(code)
    if gen_key in {"BOOMER", "SILENT", "GREATEST", "MATURE"}:
        lifestyle_score = max(lifestyle_score, 0.5)
    pain_tendency = 0.55 if lifestyle_score >= 0.5 else 0.35

    return {
        "raw": raw,
        "code": code,
        "lifestyle_contribution": round(lifestyle_score, 4),
        "pain_tendency": round(pain_tendency, 4),
        "messaging_tone": tone,
    }


def rule_016_gender(raw: str | None) -> dict:
    """Rule-016: Gender → personalization only; excluded from Purchase Power."""
    text = (raw or "").strip()
    return {
        "raw": raw,
        "personalization_value": text or None,
        "used_in_purchase_power": False,
    }


def rule_017_bank_card(raw: str | None) -> dict:
    """Rule-017: Bank Card → Brand Familiarity supporting variable only."""
    code = normalize_code(raw)
    return {
        "raw": raw,
        "code": code,
        "brand_familiarity_contribution": signal_strength(code),
    }


def compose_intermediate_intelligence(rules: dict) -> dict:
    """Section 10.5 — standardized intermediate outputs for downstream engines."""
    income = rules["rule_012"]
    home = rules["rule_013"]
    net_worth = rules["rule_009"]
    residence = rules["rule_010"]
    age = rules["rule_014"]
    generation = rules["rule_015"]
    online = rules["rule_007"]
    retail = rules["rule_008"]
    bank = rules["rule_017"]
    household = rules["rule_011"]

    income_contribution = 0.0
    if income["numeric_value"] is not None:
        income_contribution = min(1.0, income["numeric_value"] / 150_000)
    elif income.get("categorical_code"):
        from app.intelligence.datalogix import income_signal_strength

        income_contribution = income_signal_strength(str(income["categorical_code"]))

    purchase_readiness = round(
        min(
            1.0,
            net_worth["purchase_power_contribution"] * 0.35
            + home["purchase_power_contribution"] * 0.25
            + income_contribution * 0.25
            + residence["residential_stability"] * 0.15,
        ),
        4,
    )

    lifestyle_signals = round(
        min(
            1.0,
            online["digital_engagement"] * 0.25
            + residence["residential_stability"] * 0.25
            + age["life_stage_score"] * 0.25
            + generation["lifestyle_contribution"] * 0.25,
        ),
        4,
    )

    wellness_signals = round(
        min(
            1.0,
            lifestyle_signals * 0.5
            + household["family_structure_score"] * 0.3
            + (1.0 - generation["pain_tendency"]) * 0.2,
        ),
        4,
    )

    brand_signal = round(
        min(1.0, retail["brand_familiarity_contribution"] * 0.6 + bank["brand_familiarity_contribution"] * 0.4),
        4,
    )

    return {
        "digital_engagement": online["digital_engagement"],
        "digital_engagement_label": online["label"],
        "residential_stability": residence["residential_stability"],
        "family_structure": household["family_structure_score"],
        "family_messaging_hints": household["messaging_hints"],
        "purchase_readiness": purchase_readiness,
        "lifestyle_signals": lifestyle_signals,
        "wellness_signals": wellness_signals,
        "brand_familiarity_signal": brand_signal,
        "estimated_income_numeric": income["numeric_value"],
        "estimated_income_categorical": income["categorical_code"],
        "home_value_numeric": home["numeric_value"],
        "home_value_categorical": home["categorical_code"],
        "age_life_stage_score": age["life_stage_score"],
        "generation_pain_tendency": generation["pain_tendency"],
        "generation_messaging_tone": generation["messaging_tone"],
        "gender_personalization": rules["rule_016"]["personalization_value"],
        "net_worth_strength": net_worth["purchase_power_contribution"],
        "home_value_strength": home["purchase_power_contribution"],
    }


def _count(value, default=0) -> int:
    if value is None or str(value).strip() == "":
        return default
    try:
        return int(float(str(value)))
    except ValueError:
        return default


def _age_label(text: str) -> str:
    if not text:
        return "Unknown life stage"
    prefix = text[0]
    if prefix in {"7", "8", "9"}:
        return "Senior life stage"
    if prefix in {"5", "6"}:
        return "Mature adult life stage"
    if prefix in {"3", "4"}:
        return "Mid-life stage"
    return "Younger adult life stage"
