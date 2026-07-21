"""
Volume 10 — Business Rule Library (Single Source of Truth).

Every business rule executed in CIOS must be registered here with a unique Rule ID.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class BusinessRule:
    rule_id: str
    name: str
    category: str
    purpose: str
    business_owner: str = "Ceragem CIOS"
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    execution_logic: str = ""
    exceptions: str = ""
    acceptance_criteria: str = ""
    implementation_refs: tuple[str, ...] = ()
    version: str = "1.0"
    approval_status: str = "Approved"


def _rule(**kwargs) -> BusinessRule:
    return BusinessRule(**kwargs)


RULES: tuple[BusinessRule, ...] = (
    # Section 4 — Upload
    _rule(
        rule_id="RULE-UP-001",
        name="Accepted Upload File Types",
        category="UP",
        purpose="Restrict upload to supported formats.",
        inputs=("uploaded_file",),
        outputs=("upload_accepted", "upload_rejected"),
        dependencies=("Upload Module",),
        execution_logic="Allow xlsx and csv only; reject before processing.",
        acceptance_criteria="Unsupported file types are rejected before processing.",
        implementation_refs=("upload.validate_file_type",),
    ),
    _rule(
        rule_id="RULE-UP-002",
        name="Upload Size Validation",
        category="UP",
        purpose="Prevent oversized uploads.",
        inputs=("uploaded_file",),
        outputs=("upload_accepted", "upload_rejected"),
        dependencies=("Upload Module",),
        execution_logic="Maximum size 100 MB.",
        acceptance_criteria="Files exceeding the limit shall not be processed.",
        implementation_refs=("upload.validate_file_size",),
    ),
    # Section 5 — Validation
    _rule(
        rule_id="RULE-VAL-001",
        name="Email Validation",
        category="VAL",
        purpose="Verify valid email format.",
        inputs=("email_address",),
        outputs=("valid_email", "invalid_email_flag"),
        dependencies=("RULE-UP-001",),
        execution_logic="RFC-style email pattern validation.",
        acceptance_criteria="Invalid emails are flagged; records remain importable.",
        implementation_refs=("Rule-003", "RULE-VAL-001"),
    ),
    _rule(
        rule_id="RULE-VAL-002",
        name="ZIP Validation",
        category="VAL",
        purpose="Validate ZIP Code.",
        inputs=("zip_code",),
        outputs=("normalized_zip",),
        dependencies=("RULE-VAL-001",),
        execution_logic="Accept five-digit ZIP or ZIP+4; normalize to five digits.",
        acceptance_criteria="ZIP Intelligence is generated only for valid ZIPs.",
        implementation_refs=("Rule-018", "Rule-019", "RULE-VAL-002"),
    ),
    _rule(
        rule_id="RULE-VAL-003",
        name="Duplicate Customer",
        category="VAL",
        purpose="Detect duplicated customers by email address.",
        inputs=("email_address",),
        outputs=("insert", "update", "ignore"),
        dependencies=("RULE-VAL-001",),
        execution_logic="Primary key email; in-file duplicates update existing row.",
        acceptance_criteria="Duplicate policy is configurable; default updates existing customer.",
        implementation_refs=("Rule-004",),
    ),
    # Section 6 — Mapping
    _rule(
        rule_id="RULE-MAP-001",
        name="Single Internal Field Mapping",
        category="MAP",
        purpose="Every uploaded column maps to one internal field.",
        inputs=("uploaded_columns",),
        outputs=("column_map",),
        dependencies=("RULE-VAL-001",),
        execution_logic="One source header per internal field; duplicates prohibited.",
        acceptance_criteria="Duplicate mappings prohibited.",
        implementation_refs=("detect_duplicate_source_mappings",),
    ),
    _rule(
        rule_id="RULE-MAP-002",
        name="Preserve Unmapped Columns",
        category="MAP",
        purpose="Unmapped columns remain available; raw data preserved.",
        inputs=("uploaded_row",),
        outputs=("raw_customer_data",),
        dependencies=("RULE-MAP-001",),
        execution_logic="Full row JSON stored in raw_customer_data.",
        acceptance_criteria="No uploaded data is discarded.",
        implementation_refs=("RawCustomerData.json_data",),
    ),
    # Section 7 — Datalogix
    _rule(
        rule_id="RULE-DAT-001",
        name="Preserve Original Datalogix Values",
        category="DAT",
        purpose="X/Y/Z/U proprietary codes never converted to numbers.",
        inputs=("datalogix_field", "raw_value"),
        outputs=("stored_value",),
        dependencies=("RULE-MAP-001",),
        execution_logic="Store authoritative value unchanged.",
        acceptance_criteria="Uploaded value equals stored value.",
        implementation_refs=("Rule-005", "preserve_datalogix_value"),
    ),
    _rule(
        rule_id="RULE-DAT-002",
        name="Interpret Datalogix Codes",
        category="DAT",
        purpose="Interpretation occurs in Intelligence Engine only.",
        inputs=("stored_datalogix",),
        outputs=("datalogix_signals",),
        dependencies=("RULE-DAT-001",),
        execution_logic="Rules 007–017 interpret codes; DB values unchanged.",
        implementation_refs=("Rule-007", "Rule-017", "run_datalogix_engine"),
    ),
    _rule(
        rule_id="RULE-DAT-003",
        name="Prevent Numeric Conversion on Categorical Datalogix",
        category="DAT",
        purpose="No numeric conversion on categorical Datalogix fields.",
        inputs=("categorical_datalogix",),
        outputs=("preserved_code",),
        dependencies=("RULE-DAT-001",),
        acceptance_criteria="Intelligence never converts X/Y/Z/U to numbers.",
        implementation_refs=("Rule-005", "Rule-006"),
    ),
    # Section 8 — ZIP Intelligence
    _rule(
        rule_id="RULE-ZIP-001",
        name="Normalize ZIP Code",
        category="ZIP",
        purpose="ZIP+4 becomes five-digit ZIP for lookup.",
        inputs=("zip_code",),
        outputs=("normalized_zip",),
        dependencies=("RULE-DAT-002",),
        implementation_refs=("Rule-019",),
    ),
    _rule(
        rule_id="RULE-ZIP-002",
        name="Load ZIP Intelligence",
        category="ZIP",
        purpose="Enrich customer with ZIP reference data.",
        inputs=("normalized_zip",),
        outputs=("median_income", "population", "county_name", "top_50_income_zip"),
        dependencies=("RULE-ZIP-001",),
        implementation_refs=("Rule-020", "Rule-021", "Rule-022"),
    ),
    _rule(
        rule_id="RULE-ZIP-003",
        name="Premium ZIP Detection",
        category="ZIP",
        purpose="Top 50 ZIP supports Purchase Power only.",
        inputs=("top_50_income_zip",),
        outputs=("geographic_confidence",),
        dependencies=("RULE-ZIP-002",),
        acceptance_criteria="Never independently assigns Ceragem Segment.",
        implementation_refs=("Rule-022", "Rule-049"),
    ),
    # Section 9 — PRIZM Proxy
    _rule(
        rule_id="RULE-PRZ-001",
        name="Single PRIZM Proxy Segment",
        category="PRZ",
        purpose="Every customer receives one PRIZM Proxy Segment.",
        inputs=("datalogix_signals", "zip_intelligence"),
        outputs=("prizm_proxy_segment",),
        dependencies=("RULE-ZIP-003",),
        implementation_refs=("Rule-025",),
    ),
    _rule(
        rule_id="RULE-PRZ-002",
        name="Unknown Minimization",
        category="PRZ",
        purpose="Unknown assigned only after all rules evaluated.",
        inputs=("rule_results",),
        outputs=("prizm_proxy_segment",),
        dependencies=("RULE-PRZ-001",),
        implementation_refs=("Rule-026",),
    ),
    _rule(
        rule_id="RULE-PRZ-003",
        name="Deterministic PRIZM Proxy",
        category="PRZ",
        purpose="Identical inputs produce identical outputs.",
        inputs=("customer_context",),
        outputs=("prizm_proxy_segment",),
        dependencies=("RULE-PRZ-002",),
        implementation_refs=("run_prizm_proxy_engine",),
    ),
    # Section 10 — Ceragem Segment
    _rule(
        rule_id="RULE-SEG-001",
        name="Single Ceragem Segment",
        category="SEG",
        purpose="Every customer receives one Ceragem Segment.",
        outputs=("ceragem_segment",),
        dependencies=("RULE-LIF-002",),
        implementation_refs=("Rule-034",),
    ),
    _rule(
        rule_id="RULE-SEG-002",
        name="Combined Intelligence Segmentation",
        category="SEG",
        purpose="Segment from Purchase Power, Pain, Lifestyle, PRIZM, ZIP.",
        inputs=("purchase_power", "pain_index", "lifestyle", "prizm_proxy", "zip_intelligence"),
        outputs=("ceragem_segment",),
        dependencies=("RULE-PRZ-003", "RULE-PUR-002", "RULE-PAI-002", "RULE-LIF-002"),
        implementation_refs=("Rule-035", "Rule-040"),
    ),
    _rule(
        rule_id="RULE-SEG-003",
        name="Segment Strategy Not Eligibility",
        category="SEG",
        purpose="Ceragem Segment determines strategy, not eligibility.",
        outputs=("campaign_strategy",),
        dependencies=("RULE-SEG-001",),
        implementation_refs=("Rule-067",),
    ),
    # Section 11 — Purchase Power
    _rule(
        rule_id="RULE-PUR-001",
        name="Composite Purchase Power",
        category="PUR",
        purpose="Multiple indicators; no single variable decides PP.",
        inputs=("income", "home_value", "net_worth", "zip", "residence"),
        outputs=("purchase_power",),
        dependencies=("RULE-PRZ-003",),
        implementation_refs=("Rule-049", "Rule-054"),
    ),
    _rule(
        rule_id="RULE-PUR-002",
        name="Purchase Power Categories",
        category="PUR",
        purpose="Purchase Power values High, Medium, Low only.",
        outputs=("purchase_power_category",),
        dependencies=("RULE-PUR-001",),
        implementation_refs=("Rule-054",),
    ),
    # Section 12 — Pain Index
    _rule(
        rule_id="RULE-PAI-001",
        name="Therapeutic Motivation Estimate",
        category="PAI",
        purpose="Pain Index is not a medical diagnosis.",
        outputs=("pain_index",),
        dependencies=("RULE-PUR-002",),
        implementation_refs=("Rule-055", "Rule-059"),
    ),
    _rule(
        rule_id="RULE-PAI-002",
        name="Composite Pain Index",
        category="PAI",
        purpose="Pain from age, generation, lifestyle, residence, household.",
        inputs=("age_range", "generation", "lifestyle", "residence", "household"),
        outputs=("pain_index",),
        dependencies=("RULE-PAI-001",),
        implementation_refs=("Rule-055", "Rule-058", "Rule-059"),
    ),
    # Section 13 — Lifestyle
    _rule(
        rule_id="RULE-LIF-001",
        name="Wellness Orientation",
        category="LIF",
        purpose="Lifestyle estimates proactive wellness orientation.",
        outputs=("lifestyle_index",),
        dependencies=("RULE-PAI-002",),
        implementation_refs=("Rule-060", "Rule-064"),
    ),
    _rule(
        rule_id="RULE-LIF-002",
        name="Lifestyle Categories",
        category="LIF",
        purpose="Lifestyle values High, Medium, Low only.",
        outputs=("lifestyle_category",),
        dependencies=("RULE-LIF-001",),
        implementation_refs=("Rule-064",),
    ),
    # Section 14 — Recommendation
    _rule(
        rule_id="RULE-REC-001",
        name="Single Product Recommendation",
        category="REC",
        purpose="Every customer receives one primary product recommendation.",
        outputs=("recommended_product",),
        dependencies=("RULE-SEG-002",),
        implementation_refs=("Rule-065",),
    ),
    _rule(
        rule_id="RULE-REC-002",
        name="Explainable Recommendations",
        category="REC",
        purpose="Every recommendation references rule executions.",
        outputs=("trace",),
        dependencies=("RULE-REC-001",),
        implementation_refs=("IntelligenceContext.trace",),
    ),
    _rule(
        rule_id="RULE-REC-003",
        name="Recommendations Do Not Overwrite Customer Data",
        category="REC",
        purpose="Intelligence stored separately from customer facts.",
        outputs=("customer_intelligence",),
        dependencies=("RULE-REC-001",),
        implementation_refs=("CustomerIntelligence",),
    ),
    # Section 15 — Campaign
    _rule(
        rule_id="RULE-CAM-001",
        name="Campaign Begins With Intelligence",
        category="CAM",
        purpose="Campaigns built from Customer Intelligence audience.",
        dependencies=("RULE-REC-001",),
        implementation_refs=("get_campaign_audience",),
    ),
    _rule(
        rule_id="RULE-CAM-002",
        name="Campaign Forecast Required",
        category="CAM",
        purpose="Every campaign has one Forecast.",
        dependencies=("RULE-CAM-001",),
        implementation_refs=("compute_campaign_forecast",),
    ),
    _rule(
        rule_id="RULE-CAM-003",
        name="Campaign Learning Record",
        category="CAM",
        purpose="Every completed campaign has one Learning Record.",
        dependencies=("RULE-CAM-002",),
        implementation_refs=("create_campaign_learning_record",),
    ),
    # Section 16 — Forecast
    _rule(
        rule_id="RULE-FOR-001",
        name="Expected Orders",
        category="FOR",
        purpose="Expected Orders = Target Customers × Expected Conversion Rate.",
        inputs=("target_customers", "expected_conversion_rate"),
        outputs=("expected_orders",),
        dependencies=("RULE-CAM-002",),
        execution_logic="target_customers * conversion_rate",
        implementation_refs=("Rule-068",),
    ),
    _rule(
        rule_id="RULE-FOR-002",
        name="Expected Revenue",
        category="FOR",
        purpose="Expected Revenue = Expected Orders × Average Product Price.",
        inputs=("expected_orders", "product_price"),
        outputs=("expected_revenue",),
        dependencies=("RULE-FOR-001",),
        execution_logic="expected_orders * product_price",
        implementation_refs=("Rule-069",),
    ),
    _rule(
        rule_id="RULE-FOR-003",
        name="Le Frame Incentive",
        category="FOR",
        purpose="Le Frame Incentive = Expected Revenue × 15%.",
        inputs=("expected_revenue",),
        outputs=("expected_incentive",),
        dependencies=("RULE-FOR-002",),
        execution_logic="expected_revenue * 0.15",
        implementation_refs=("Rule-070",),
    ),
    _rule(
        rule_id="RULE-FOR-004",
        name="Forecast Accuracy",
        category="FOR",
        purpose="Forecast Accuracy = Actual Revenue ÷ Expected Revenue.",
        inputs=("actual_revenue", "expected_revenue"),
        outputs=("forecast_accuracy",),
        dependencies=("RULE-FOR-002",),
        execution_logic="actual_revenue / expected_revenue",
        implementation_refs=("forecast_accuracy",),
    ),
    # Section 17 — Learning
    _rule(
        rule_id="RULE-LRN-001",
        name="Learning Record On Completion",
        category="LRN",
        purpose="Every completed campaign creates one Learning Record.",
        dependencies=("Campaign Report Import",),
        implementation_refs=("create_learning_records_for_report",),
    ),
    _rule(
        rule_id="RULE-LRN-002",
        name="Immutable Learning Records",
        category="LRN",
        purpose="Learning Records are never updated after creation.",
        dependencies=("RULE-LRN-001",),
        implementation_refs=("CampaignLearning",),
    ),
    _rule(
        rule_id="RULE-LRN-003",
        name="Historical Learning Preservation",
        category="LRN",
        purpose="Historical learning data is never recalculated.",
        dependencies=("RULE-LRN-002",),
        implementation_refs=("CampaignLearning",),
    ),
)

RULE_REGISTRY: dict[str, BusinessRule] = {r.rule_id: r for r in RULES}

# Section 18 — deterministic execution order (business categories)
EXECUTION_ORDER: tuple[str, ...] = (
    "Upload",
    "Validation",
    "Mapping",
    "Database",
    "Datalogix",
    "ZIP Intelligence",
    "PRIZM Proxy",
    "Purchase Power",
    "Pain Index",
    "Lifestyle",
    "Ceragem Segment",
    "Recommendation",
    "Campaign",
    "Forecast",
    "Export",
    "Campaign Report",
    "Learning",
)

# Section 19 — dependency matrix (category → depends on)
DEPENDENCY_MATRIX: dict[str, tuple[str, ...]] = {
    "Validation": ("Upload",),
    "Mapping": ("Validation",),
    "Datalogix": ("Mapping",),
    "ZIP Intelligence": ("Datalogix",),
    "PRIZM Proxy": ("ZIP Intelligence",),
    "Purchase Power": ("PRIZM Proxy",),
    "Pain Index": ("Purchase Power",),
    "Lifestyle": ("Pain Index",),
    "Ceragem Segment": ("Lifestyle",),
    "Recommendation": ("Ceragem Segment",),
    "Campaign": ("Recommendation",),
    "Forecast": ("Campaign",),
    "Learning": ("Campaign Report",),
}

# Map Volume 04 implementation rule IDs → Volume 10 business rule IDs
IMPLEMENTATION_TO_BUSINESS: dict[str, str] = {
    "Rule-003": "RULE-VAL-001",
    "Rule-004": "RULE-VAL-003",
    "Rule-005": "RULE-DAT-001",
    "Rule-018": "RULE-VAL-002",
    "Rule-019": "RULE-ZIP-001",
    "Rule-020": "RULE-ZIP-002",
    "Rule-021": "RULE-ZIP-002",
    "Rule-022": "RULE-ZIP-003",
    "Rule-025": "RULE-PRZ-001",
    "Rule-026": "RULE-PRZ-002",
    "Rule-034": "RULE-SEG-001",
    "Rule-049": "RULE-ZIP-003",
    "Rule-054": "RULE-PUR-001",
    "Rule-055": "RULE-PAI-002",
    "Rule-059": "RULE-PAI-002",
    "Rule-060": "RULE-LIF-001",
    "Rule-064": "RULE-LIF-002",
    "Rule-065": "RULE-REC-001",
    "Rule-068": "RULE-FOR-001",
    "Rule-069": "RULE-FOR-002",
    "Rule-070": "RULE-FOR-003",
}

# Dashboard metrics → business rules (Section 21 traceability)
DASHBOARD_RULE_MAP: dict[str, str] = {
    "target_customers": "RULE-CAM-001",
    "total_customers": "RULE-CAM-001",
    "expected_revenue": "RULE-FOR-002",
    "le_frame_incentive": "RULE-FOR-003",
    "campaign_roi": "RULE-FOR-004",
    "forecast_accuracy": "RULE-FOR-004",
    "recommended_product": "RULE-REC-001",
    "prizm_proxy_segment": "RULE-PRZ-001",
    "ceragem_segment": "RULE-SEG-001",
}

AI_RULE_MAP: dict[str, str] = {
    "product_recommendation": "RULE-REC-001",
    "message_recommendation": "RULE-REC-002",
    "campaign_recommendation": "RULE-REC-003",
    "purchase_power": "RULE-PUR-001",
    "pain_index": "RULE-PAI-002",
    "revenue_prediction": "RULE-FOR-002",
    "conversion_prediction": "RULE-FOR-004",
}

CALCULATION_FRAMEWORK_MAP: dict[str, str] = {
    "purchase_power": "RULE-PUR-001",
    "pain_index": "RULE-PAI-001",
    "lifestyle": "RULE-LIF-001",
    "prizm_proxy": "RULE-PRZ-001",
    "ceragem_segment": "RULE-SEG-001",
    "recommendation": "RULE-REC-001",
    "revenue": "RULE-FOR-002",
    "conversion": "RULE-FOR-004",
    "campaign_priority": "RULE-CAM-001",
}


def get_rule(rule_id: str) -> BusinessRule | None:
    return RULE_REGISTRY.get(rule_id)


def rules_by_category(prefix: str) -> list[BusinessRule]:
    return [r for r in RULES if r.category == prefix]


def resolve_business_rule_id(implementation_rule_id: str) -> str | None:
    if implementation_rule_id in RULE_REGISTRY:
        return implementation_rule_id
    if implementation_rule_id in IMPLEMENTATION_TO_BUSINESS:
        return IMPLEMENTATION_TO_BUSINESS[implementation_rule_id]
    for rule in RULES:
        if implementation_rule_id in rule.implementation_refs:
            return rule.rule_id
    return None


def all_rule_ids() -> Iterable[str]:
    return RULE_REGISTRY.keys()
