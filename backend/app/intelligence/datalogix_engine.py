"""Datalogix Intelligence Engine — Section 10 (Rules 005, 007–017)."""

from app.intelligence.datalogix import normalize_code
from app.intelligence.datalogix_rules import (
    compose_intermediate_intelligence,
    rule_007_online_access,
    rule_008_retail_card,
    rule_009_net_worth,
    rule_010_length_of_residence,
    rule_011_household_composition,
    rule_012_estimated_income,
    rule_013_home_value,
    rule_014_age_range,
    rule_015_generation,
    rule_016_gender,
    rule_017_bank_card,
)
from app.intelligence.normalization import apply_rule_006_numeric
from app.intelligence.types import IntelligenceContext

CATEGORICAL_FIELDS = {
    "net_worth", "online_access", "retail_card", "bank_card",
    "age_range", "generation", "gender", "dwelling",
}

# Section 10.3 — attribute to internal storage field (DB column names)
FIELD_ALIASES = {
    "net_worth_indicator": "net_worth",
    "dwelling_type": "dwelling",
    "household_composition": "household",
}


def preserve_datalogix_value(field: str, value: str | None) -> str | None:
    """Rule-005 / Principle D-001: Store authoritative Datalogix values unchanged."""
    if field == "dma_code":
        from app.reference.nielsen_dma import normalize_dma_code

        return normalize_dma_code(value)
    if field == "county_code":
        if not value or not str(value).strip():
            return None
        text = str(value).strip().upper()
        if text in {"", "X", "XXXX"}:
            return None
        return text
    if not value or not str(value).strip():
        return None
    text = str(value).strip()
    if field in CATEGORICAL_FIELDS or text.upper() in {"X", "Y", "Z", "U"}:
        return text.upper()
    normalized = apply_rule_006_numeric(text)
    return str(normalized) if normalized is not None else None


def _raw_field(raw: dict, *keys: str) -> str | None:
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return None


def to_signal_dict(raw: dict[str, str | None]) -> dict:
    """Legacy-compatible signal view derived from intermediate intelligence."""
    intermediate = raw.get("_intermediate") or {}
    rules = raw.get("_rules") or {}
    income = rules.get("rule_012", {})
    home = rules.get("rule_013", {})

    return {
        "net_worth_indicator": normalize_code(_raw_field(raw, "net_worth")),
        "online_access_code": normalize_code(_raw_field(raw, "online_access")),
        "retail_card_code": normalize_code(_raw_field(raw, "retail_card")),
        "bank_card_code": normalize_code(_raw_field(raw, "bank_card")),
        "home_value_code": normalize_code(_raw_field(raw, "home_value")),
        "estimated_income_code": _raw_field(raw, "estimated_income") or "",
        "estimated_income_numeric": income.get("numeric_value"),
        "generation": normalize_code(_raw_field(raw, "generation")),
        "age_range": _raw_field(raw, "age_range") or "",
        "length_of_residence": normalize_code(_raw_field(raw, "length_of_residence")),
        "adults_in_household": _raw_field(raw, "adults") or "",
        "children_in_household": _raw_field(raw, "children") or "",
        "persons_in_household": _raw_field(raw, "persons") or "",
        "household_composition": _raw_field(raw, "household") or "",
        "dwelling_type": _raw_field(raw, "dwelling") or "",
        "gender": _raw_field(raw, "gender") or "",
        "intermediate": intermediate,
    }


def run_datalogix_engine(ctx: IntelligenceContext) -> None:
    """
    Section 10.4 workflow:
    Read → Load → Preserve → Interpret → Intermediate Intelligence → Pass downstream.
    """
    raw = ctx.datalogix_raw

    ctx.add_trace(
        "Rule-005", "Datalogix Preservation Rule",
        {"raw": {k: v for k, v in raw.items() if not k.startswith("_")}},
        {"stored_as_received": True},
        "Original Datalogix values preserved; database stores authoritative source only.",
    )

    rules = {
        "rule_007": rule_007_online_access(_raw_field(raw, "online_access")),
        "rule_008": rule_008_retail_card(_raw_field(raw, "retail_card")),
        "rule_009": rule_009_net_worth(_raw_field(raw, "net_worth")),
        "rule_010": rule_010_length_of_residence(_raw_field(raw, "length_of_residence")),
        "rule_011": rule_011_household_composition(
            adults=_raw_field(raw, "adults"),
            children=_raw_field(raw, "children"),
            persons=_raw_field(raw, "persons"),
            household=_raw_field(raw, "household"),
        ),
        "rule_012": rule_012_estimated_income(_raw_field(raw, "estimated_income")),
        "rule_013": rule_013_home_value(_raw_field(raw, "home_value")),
        "rule_014": rule_014_age_range(_raw_field(raw, "age_range")),
        "rule_015": rule_015_generation(_raw_field(raw, "generation")),
        "rule_016": rule_016_gender(_raw_field(raw, "gender")),
        "rule_017": rule_017_bank_card(_raw_field(raw, "bank_card")),
    }

    intermediate = compose_intermediate_intelligence(rules)
    ctx.datalogix_intermediate = intermediate

    enriched_raw = dict(raw)
    enriched_raw["_rules"] = rules
    enriched_raw["_intermediate"] = intermediate
    ctx.datalogix_signals = to_signal_dict(enriched_raw)

    for rule_id, rule_key, name in (
        ("Rule-007", "rule_007", "Online Access Intelligence Rule"),
        ("Rule-008", "rule_008", "Retail Card Intelligence Rule"),
        ("Rule-009", "rule_009", "Net Worth Indicator Rule"),
        ("Rule-010", "rule_010", "Length of Residence Rule"),
        ("Rule-011", "rule_011", "Household Composition Rule"),
        ("Rule-012", "rule_012", "Estimated Income Rule"),
        ("Rule-013", "rule_013", "Home Value Rule"),
        ("Rule-014", "rule_014", "Age Range Rule"),
        ("Rule-015", "rule_015", "Generation Rule"),
        ("Rule-016", "rule_016", "Gender Rule"),
        ("Rule-017", "rule_017", "Bank Card Rule"),
    ):
        ctx.add_trace(rule_id, name, rules[rule_key], rules[rule_key], f"{name} applied; raw values unchanged.")

    ctx.add_trace(
        "Rule-DX", "Datalogix Intelligence Engine",
        {"attributes_loaded": list(raw.keys())},
        intermediate,
        "Intermediate intelligence generated for downstream engines.",
    )
