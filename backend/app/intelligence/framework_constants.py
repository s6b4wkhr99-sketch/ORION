"""Volume 19 — Intelligence Calculation Framework constants."""

CALCULATION_VERSION = "Volume 19 v1.2"
CALCULATION_VERSION_PRE_SKU_MIGRATION = "Volume 19 v1.0"
INTELLIGENCE_ENGINE_VERSION = "Volume 04 Pipeline + Volume 19 Framework"
RULE_VERSION_DEFAULT = "Volume 04 Rules 001–070 + SKU Migration 2026.07 + Promo Policy v2"

INTELLIGENCE_CATEGORIES: tuple[str, ...] = (
    "purchase_power",
    "pain_index",
    "lifestyle",
    "digital_engagement",
    "brand_familiarity",
    "sleep_affinity",
    "prizm_proxy",
    "ceragem_segment",
    "recommendation",
    "conversion",
    "revenue",
    "campaign_priority",
)

# Volume 04 Ceragem segment → Volume 19 commercial taxonomy (from RDL)
from app.reference.registry import CERAGEM_V19_MAP

PRIORITY_TO_GRADE: dict[str, str] = {
    "High": "A",
    "Medium": "B",
    "Low": "C",
}

COMPOSITE_RULE_IDS: dict[str, str] = {
    "purchase_power": "Rule-054",
    "pain_index": "Rule-059",
    "lifestyle": "Rule-064",
    "recommendation": "Rule-066",
}

CATEGORY_BUSINESS_RULES: dict[str, str] = {
    "purchase_power": "RULE-PUR-001",
    "pain_index": "RULE-PAI-001",
    "lifestyle": "RULE-LIF-001",
    "digital_engagement": "RULE-DIG-001",
    "brand_familiarity": "RULE-BRD-001",
    "sleep_affinity": "RULE-SLP-001",
    "prizm_proxy": "RULE-PRZ-001",
    "ceragem_segment": "RULE-SEG-001",
    "recommendation": "RULE-REC-001",
    "conversion": "RULE-FOR-004",
    "revenue": "RULE-FOR-002",
    "campaign_priority": "RULE-CAM-001",
}
