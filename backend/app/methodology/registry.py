"""Volume 20 — Le Frame methodology registry and volume mapping."""

METHODOLOGY_VERSION = "Volume 20 v1.0"
METHODOLOGY_OWNER = "Le Frame"

PHILOSOPHY = (
    "Customers do not purchase because they received an email. "
    "Customers purchase when the right product, the right message and the right timing "
    "meet the right customer. Customer Intelligence is the objective."
)

INTELLIGENCE_PYRAMID: tuple[dict, ...] = (
    {"level": 1, "name": "Raw Customer Data", "value": "operational"},
    {"level": 2, "name": "Standardized Customer Data", "value": "operational"},
    {"level": 3, "name": "Enriched Customer Profile", "value": "tactical"},
    {"level": 4, "name": "Customer Intelligence", "value": "strategic"},
    {"level": 5, "name": "Campaign Intelligence", "value": "strategic"},
    {"level": 6, "name": "Business Recommendation", "value": "decision"},
    {"level": 7, "name": "Executive Intelligence", "value": "decision"},
)

INTELLIGENCE_LAYERS: tuple[dict, ...] = (
    {
        "layer": 1,
        "name": "Raw Customer Data",
        "module": "app.acquisition.upload",
        "volume": "04/08",
        "outputs": ["customers", "raw_upload", "field_mapping"],
    },
    {
        "layer": 2,
        "name": "Geographic Intelligence",
        "module": "app.intelligence.zip_engine",
        "volume": "04/09",
        "outputs": ["purchase_opportunity", "premium_potential", "campaign_opportunity"],
    },
    {
        "layer": 3,
        "name": "Behavioral Intelligence",
        "module": "app.intelligence.datalogix_engine",
        "volume": "04",
        "outputs": ["categorical_signals", "preserved_datalogix_codes"],
    },
    {
        "layer": 4,
        "name": "Commercial Intelligence",
        "module": "app.intelligence.calculation_framework",
        "volume": "04/19",
        "outputs": ["purchase_power", "pain_index", "lifestyle", "prizm_proxy", "ceragem_segment"],
    },
    {
        "layer": 5,
        "name": "Campaign Intelligence",
        "module": "app.campaign.analytics",
        "volume": "06/15",
        "outputs": ["campaign_performance", "funnel", "learning_insights"],
    },
    {
        "layer": 6,
        "name": "Executive Intelligence",
        "module": "app.analytics.executive",
        "volume": "17",
        "outputs": ["executive_kpi", "insights", "recommendations", "scorecard"],
    },
    {
        "layer": 7,
        "name": "Continuous Learning",
        "module": "app.learning.campaign_learning",
        "volume": "06/18",
        "outputs": ["forecast_accuracy", "learning_score", "recommendation_weights"],
    },
)

DECISION_MODEL = {
    "traditional_crm": ["Customer", "Campaign"],
    "le_frame": [
        "Customer",
        "Customer Intelligence",
        "Recommendation",
        "Campaign",
        "Learning",
        "Customer Intelligence",
    ],
}

CONVERSION_STAGES: tuple[str, ...] = (
    "Delivered",
    "Opened",
    "Clicked",
    "Product Exploration",
    "Consultation",
    "Purchase Intent",
    "Purchase",
    "Repeat Purchase",
    "Advocacy",
)

EXECUTIVE_QUESTIONS: tuple[str, ...] = (
    "Which State should receive additional investment?",
    "Which ZIPs should be prioritized?",
    "Which product should be promoted?",
    "Which campaign should be repeated?",
    "Which segment is growing?",
    "Which segment is declining?",
    "Where should marketing budget increase?",
)

STRATEGIC_DIFFERENTIATION = {
    "traditional_crm": "Who is the customer?",
    "traditional_esp": "Who received the email?",
    "cios": (
        "Who is most likely to purchase, why, when, through which message, "
        "using which product, in which geography, and with what expected revenue?"
    ),
}

HIGH_CONSIDERATION_PRODUCTS: tuple[str, ...] = (
    "Medical Wellness",
    "Luxury Wellness",
    "Premium Home Healthcare",
    "Professional Equipment",
    "Enterprise B2B Solutions",
)

from app.reference.registry import CERAGEM_SEGMENT_V19

CERAGEM_SEGMENTS: tuple[str, ...] = tuple(segment[0] for segment in CERAGEM_SEGMENT_V19)

PRIZM_PROXY_OUTPUTS: tuple[str, ...] = (
    "Lifestyle Orientation",
    "Household Pattern",
    "Wellness Affinity",
    "Digital Affinity",
    "Commercial Potential",
)

GEOGRAPHIC_OUTPUTS: tuple[str, ...] = (
    "Purchase Opportunity",
    "Regional Affinity",
    "Premium Potential",
    "Campaign Opportunity",
)

EXPLAINABILITY_REQUIREMENTS: tuple[str, ...] = (
    "What was recommended?",
    "Why was it recommended?",
    "Which Business Rules contributed?",
    "What confidence does the recommendation have?",
    "Which historical campaigns influenced it?",
)

GOVERNANCE_REQUIREMENTS: tuple[str, ...] = (
    "Business Validation",
    "Rule Review",
    "Executive Approval",
    "Documentation Update",
    "Regression Testing",
)

SUCCESS_CRITERIA: tuple[dict, ...] = (
    {"id": "SC-01", "criterion": "Raw customer data transformed into actionable intelligence", "module": "app.acquisition.upload", "api": "/api/v1/customers/upload"},
    {"id": "SC-02", "criterion": "Intelligence is explainable", "module": "app.intelligence.calculation_framework", "api": "/api/v1/intelligence/framework/{customer_id}"},
    {"id": "SC-03", "criterion": "Recommendations are consistent", "module": "app.ai_engine.engine", "api": "/api/v1/intelligence/recommendation/{customer_id}"},
    {"id": "SC-04", "criterion": "Campaign planning is data-driven", "module": "app.campaign.forecast", "api": "/api/v1/campaign/{campaign_id}/forecast"},
    {"id": "SC-05", "criterion": "Forecast accuracy improves over time", "module": "app.learning.campaign_learning", "api": "/api/v1/analytics/learning"},
    {"id": "SC-06", "criterion": "Executive decision-making is measurable", "module": "app.analytics.executive", "api": "/api/v1/analytics/executive"},
    {"id": "SC-07", "criterion": "Campaign learning improves future recommendations", "module": "app.ai_engine.learning", "api": "/api/v1/analytics/recommendations"},
    {"id": "SC-08", "criterion": "Common intelligence framework across modules", "module": "app.intelligence.calculation_framework", "api": "/api/v1/methodology"},
)

VOLUME_DEPENDENCIES: tuple[str, ...] = (
    "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
)
