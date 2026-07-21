"""Volume 21 — Master index, cross reference and knowledge governance registry."""

KNOWLEDGE_VERSION = "Volume 21 v1.0"
KNOWLEDGE_OWNER = "Ceragem CIOS"

DOCUMENTATION_STRUCTURE = {
    "root": "CIOS",
    "readme": "README.md",
    "docs": "docs/",
    "spec": "spec/",
    "database": "database/",
    "api": "api/",
    "test": "backend/tests/",
    "assets": "assets/",
}

DOCUMENT_VOLUMES: tuple[dict, ...] = (
    {"volume": "01", "title": "Executive Proposal", "file": "docs/01_Executive_Proposal.md", "status": "approved"},
    {"volume": "02", "title": "Platform Architecture", "file": "docs/02_Platform_Architecture.md", "status": "approved"},
    {"volume": "03", "title": "Database Architecture", "file": "docs/03_Database_Architecture.md", "status": "approved"},
    {"volume": "04", "title": "Intelligence Engine", "file": "docs/04_Intelligence_Engine.md", "status": "approved"},
    {"volume": "05", "title": "UX/UI Specification", "file": "docs/05_UX_UI_Specification.md", "status": "approved"},
    {"volume": "06", "title": "Campaign Operating System", "file": "docs/06_Campaign_Operating_System.md", "status": "approved"},
    {"volume": "07", "title": "API Specification", "file": "docs/07_API_Specification.md", "status": "approved"},
    {"volume": "08", "title": "Cursor Development Guide", "file": "docs/08_Cursor_Development_Guide.md", "status": "approved"},
    {"volume": "09", "title": "Field Mapping", "file": "docs/09_Field_Mapping_Data_Dictionary.md", "status": "approved"},
    {"volume": "10", "title": "Business Rule Library", "file": "docs/10_Business_Rule_Library.md", "status": "approved"},
    {"volume": "11", "title": "Security & Governance", "file": "docs/11_Security_Permission_Governance.md", "status": "approved"},
    {"volume": "12", "title": "Testing & QA", "file": "docs/12_Testing_QA_Specification.md", "status": "approved"},
    {"volume": "13", "title": "Deployment & DevOps", "file": "docs/13_Deployment_DevOps_Specification.md", "status": "approved"},
    {"volume": "14", "title": "Operations Manual", "file": "docs/14_System_Administration_Operations_Manual.md", "status": "approved"},
    {"volume": "15", "title": "Provider Integration", "file": "docs/15_Provider_Integration_Specification.md", "status": "approved"},
    {"volume": "16", "title": "Physical Database", "file": "docs/16_Database_ERD_Physical_Schema.md", "status": "approved"},
    {"volume": "17", "title": "Executive Analytics", "file": "docs/17_Analytics_Executive_Intelligence.md", "status": "approved"},
    {"volume": "18", "title": "AI Recommendation Engine", "file": "docs/18_AI_Intelligence_Recommendation_Engine.md", "status": "approved"},
    {"volume": "19", "title": "Intelligence Calculation Framework", "file": "docs/19_Intelligence_Calculation_Framework.md", "status": "approved"},
    {"volume": "20", "title": "Le Frame Methodology", "file": "docs/20_Le_Frame_Customer_Intelligence_Methodology.md", "status": "approved"},
    {"volume": "21", "title": "Master Index", "file": "docs/21_Master_Index_Cross_Reference_Knowledge_Governance.md", "status": "approved"},
    {"volume": "22", "title": "Reference Data Library", "file": "docs/22_Reference_Data_Library.md", "status": "approved"},
    {"volume": "23", "title": "Project README", "file": "docs/23_Project_README.md", "status": "approved"},
    {"volume": "24", "title": "Development Convention", "file": "docs/24_Development_Convention.md", "status": "approved"},
    {"volume": "25", "title": "Git Workflow & Release Management", "file": "docs/25_Git_Workflow_Release_Management.md", "status": "approved"},
    {"volume": "26", "title": "CIOS Design Principles", "file": "docs/26_CIOS_Design_Principles.md", "status": "approved"},
)

MASTER_NAVIGATION: tuple[str, ...] = (
    "Executive",
    "Customer Intelligence",
    "Campaign",
    "Forecast",
    "Export",
    "Campaign Report",
    "Learning",
    "Executive Analytics",
    "Recommendation",
    "Continuous Improvement",
)

DOCUMENTATION_DEPENDENCY_MAP: tuple[dict, ...] = (
    {"name": "Executive Proposal", "volume": "01", "dependsOn": []},
    {"name": "Platform Architecture", "volume": "02", "dependsOn": ["01"]},
    {"name": "Database Architecture", "volume": "03", "dependsOn": ["02"]},
    {"name": "Intelligence Engine", "volume": "04", "dependsOn": ["03"]},
    {"name": "Field Mapping", "volume": "09", "dependsOn": ["04"]},
    {"name": "Business Rules", "volume": "10", "dependsOn": ["09"]},
    {"name": "AI Recommendation", "volume": "18", "dependsOn": ["10", "04"]},
    {"name": "Campaign OS", "volume": "06", "dependsOn": ["04", "10"]},
    {"name": "Dashboard", "volume": "05", "dependsOn": ["06", "17"]},
    {"name": "API", "volume": "07", "dependsOn": ["05", "06"]},
    {"name": "Deployment", "volume": "13", "dependsOn": ["07"]},
    {"name": "Operations", "volume": "14", "dependsOn": ["13"]},
)

DATABASE_CROSS_REFERENCE: tuple[dict, ...] = (
    {"table": "customer", "physical": "customers", "volume": "16", "module": "app.models.customer"},
    {"table": "customer_intelligence", "physical": "customer_intelligence", "volume": "16", "module": "app.models.customer"},
    {"table": "campaign", "physical": "campaign", "volume": "16", "module": "app.models.campaign"},
    {"table": "campaign_target", "physical": "campaign_target", "volume": "16", "module": "app.models.campaign"},
    {"table": "campaign_report", "physical": "campaign_report", "volume": "16", "module": "app.models.campaign"},
    {"table": "campaign_learning", "physical": "campaign_learning", "volume": "16", "module": "app.models.learning"},
    {"table": "recommendation", "physical": "recommendation", "volume": "16", "module": "app.models.recommendation"},
    {"table": "upload_history", "physical": "upload_history", "volume": "16", "module": "app.models.raw"},
    {"table": "provider", "physical": "provider", "volume": "16", "module": "app.models.provider"},
    {"table": "provider_mapping", "physical": "provider_field_mapping", "volume": "16", "module": "app.models.provider_mapping"},
    {"table": "audit_log", "physical": "audit_log", "volume": "16", "module": "app.security.audit"},
    {"table": "role", "physical": "role", "volume": "16", "module": "app.security.roles"},
    {"table": "permission", "physical": "permission", "volume": "16", "module": "app.security.roles"},
    {"table": "product_master", "physical": "product_master", "volume": "22", "module": "app.models.reference_data"},
    {"table": "state_master", "physical": "state_master", "volume": "22", "module": "app.models.reference_data"},
    {"table": "zip_master", "physical": "zip_master", "volume": "22", "module": "app.models.reference_data"},
    {"table": "ceragem_segment_master", "physical": "ceragem_segment_master", "volume": "22", "module": "app.models.reference_data"},
    {"table": "purchase_power_master", "physical": "purchase_power_master", "volume": "22", "module": "app.models.reference_data"},
)

INTELLIGENCE_CROSS_REFERENCE: tuple[dict, ...] = (
    {"intelligence": "Purchase Power", "volumes": ("04", "19"), "module": "app.intelligence.calculation_framework"},
    {"intelligence": "Pain Index", "volumes": ("04", "19"), "module": "app.intelligence.calculation_framework"},
    {"intelligence": "Lifestyle", "volumes": ("04", "19"), "module": "app.intelligence.calculation_framework"},
    {"intelligence": "PRIZM Proxy", "volumes": ("04", "19"), "module": "app.intelligence.prizm_proxy"},
    {"intelligence": "Ceragem Segment", "volumes": ("04", "19"), "module": "app.intelligence.calculation_framework"},
    {"intelligence": "Recommendation", "volumes": ("18",), "module": "app.ai_engine.engine"},
    {"intelligence": "Campaign Priority", "volumes": ("18",), "module": "app.ai_engine.engine"},
    {"intelligence": "Revenue Prediction", "volumes": ("18",), "module": "app.ai_engine.engine"},
    {"intelligence": "Conversion Prediction", "volumes": ("18",), "module": "app.ai_engine.engine"},
)

BUSINESS_RULE_CROSS_REFERENCE: tuple[dict, ...] = (
    {"category": "Upload", "prefix": "UP", "volume": "10", "module": "app.acquisition.upload"},
    {"category": "Validation", "prefix": "VAL", "volume": "10", "module": "app.acquisition.upload"},
    {"category": "Mapping", "prefix": "MAP", "volume": "10", "module": "app.mapping.data_dictionary"},
    {"category": "Datalogix", "prefix": "DAT", "volume": "10", "module": "app.intelligence.datalogix_engine"},
    {"category": "ZIP Intelligence", "prefix": "ZIP", "volume": "10", "module": "app.intelligence.zip_engine"},
    {"category": "PRIZM Proxy", "prefix": "PRZ", "volume": "10", "module": "app.intelligence.prizm_proxy"},
    {"category": "Purchase Power", "prefix": "PUR", "volume": "10", "module": "app.intelligence.calculation_framework"},
    {"category": "Pain Index", "prefix": "PAI", "volume": "10", "module": "app.intelligence.calculation_framework"},
    {"category": "Lifestyle", "prefix": "LIF", "volume": "10", "module": "app.intelligence.calculation_framework"},
    {"category": "Recommendation", "prefix": "REC", "volume": "10", "module": "app.ai_engine.engine"},
    {"category": "Campaign", "prefix": "CAM", "volume": "10", "module": "app.campaign.detail"},
    {"category": "Forecast", "prefix": "FOR", "volume": "10", "module": "app.campaign.forecast"},
    {"category": "Learning", "prefix": "LRN", "volume": "10", "module": "app.learning.campaign_learning"},
)

DASHBOARD_CROSS_REFERENCE: tuple[dict, ...] = (
    {"dashboard": "Executive Dashboard", "volumes": ("05", "17"), "api": "/api/v1/dashboard/executive"},
    {"dashboard": "Customer Dashboard", "volumes": ("05",), "api": "/api/v1/dashboard/customer"},
    {"dashboard": "Campaign Dashboard", "volumes": ("06",), "api": "/api/v1/dashboard/campaigns"},
    {"dashboard": "State Dashboard", "volumes": ("05", "17"), "api": "/api/v1/dashboard/state"},
    {"dashboard": "ZIP Dashboard", "volumes": ("05", "17"), "api": "/api/v1/dashboard/zip"},
    {"dashboard": "ROI Dashboard", "volumes": ("05", "17"), "api": "/api/v1/dashboard/roi"},
    {"dashboard": "Analytics Dashboard", "volumes": ("17",), "api": "/api/v1/analytics/executive"},
)

API_CROSS_REFERENCE: tuple[dict, ...] = (
    {"domain": "Authentication", "volume": "07", "prefix": "/api/v1/auth"},
    {"domain": "Customer", "volume": "07", "prefix": "/api/v1/customers"},
    {"domain": "Campaign", "volume": "07", "prefix": "/api/v1/campaign"},
    {"domain": "Forecast", "volume": "07", "prefix": "/api/v1/forecast"},
    {"domain": "Recommendation", "volume": "18", "prefix": "/api/v1/intelligence/recommendation"},
    {"domain": "Dashboard", "volume": "07", "prefix": "/api/v1/dashboard"},
    {"domain": "Provider", "volume": "15", "prefix": "/api/v1/providers"},
    {"domain": "Analytics", "volume": "17", "prefix": "/api/v1/analytics"},
    {"domain": "Methodology", "volume": "20", "prefix": "/api/v1/methodology"},
    {"domain": "Knowledge", "volume": "21", "prefix": "/api/v1/knowledge"},
)

WORKFLOW_CROSS_REFERENCE: tuple[dict, ...] = (
    {"workflow": "Customer Upload", "volumes": ("06", "08", "14"), "apis": ("/api/v1/customers/upload",)},
    {"workflow": "Campaign Creation", "volumes": ("06", "17"), "apis": ("/api/v1/campaign",)},
    {"workflow": "Forecast", "volumes": ("06", "19"), "apis": ("/api/v1/campaign/{campaign_id}/forecast", "/api/v1/forecast/revenue")},
    {"workflow": "Recommendation", "volumes": ("18", "19"), "apis": ("/api/v1/intelligence/recommendation/{customer_id}",)},
    {"workflow": "Export", "volumes": ("15",), "apis": ("/api/v1/export",)},
    {"workflow": "Campaign Report", "volumes": ("06", "15"), "apis": ("/api/v1/report/upload",)},
    {"workflow": "Learning", "volumes": ("18", "19"), "apis": ("/api/v1/analytics/learning", "/api/v1/learning/insights")},
)

COMPONENT_LIBRARY: tuple[dict, ...] = (
    {"component": "Cards", "volume": "05"},
    {"component": "Tables", "volume": "05"},
    {"component": "Charts", "volume": "05"},
    {"component": "Maps", "volume": "05"},
    {"component": "Filters", "volume": "05"},
    {"component": "Dropdowns", "volume": "05"},
    {"component": "Buttons", "volume": "05"},
    {"component": "Inputs", "volume": "05"},
    {"component": "Dialogs", "volume": "05"},
    {"component": "Tabs", "volume": "05"},
    {"component": "Accordions", "volume": "05"},
    {"component": "Progress Indicators", "volume": "05"},
    {"component": "Heat Maps", "volume": "05"},
    {"component": "Ranking Tables", "volume": "05"},
    {"component": "Export Components", "volume": "05"},
)

PROVIDER_INDEX: tuple[dict, ...] = (
    {"provider": "Generic CSV", "volume": "15", "module": "app.providers.adapter"},
    {"provider": "Mailchimp", "volume": "15", "module": "app.providers.adapter"},
    {"provider": "Klaviyo", "volume": "15", "module": "app.providers.adapter"},
    {"provider": "HubSpot", "volume": "15", "module": "app.providers.adapter"},
    {"provider": "Attentive", "volume": "15", "module": "app.providers.adapter"},
    {"provider": "Salesforce Marketing Cloud", "volume": "15", "module": "app.providers.adapter"},
)

DATA_SOURCE_INDEX: tuple[dict, ...] = (
    {"source": "Customer Upload", "volumes": ("03", "09", "16"), "module": "app.acquisition.upload"},
    {"source": "ZIP Intelligence", "volumes": ("03", "09", "16"), "module": "app.intelligence.zip_engine"},
    {"source": "Datalogix", "volumes": ("03", "09", "16"), "module": "app.intelligence.datalogix_engine"},
    {"source": "Campaign Reports", "volumes": ("03", "09", "16"), "module": "app.campaign.reports"},
    {"source": "Provider Data", "volumes": ("03", "09", "16"), "module": "app.providers.adapter"},
    {"source": "Learning Database", "volumes": ("03", "09", "16"), "module": "app.learning.campaign_learning"},
    {"source": "Reference Data", "volumes": ("03", "09", "16", "22"), "module": "app.reference.seed"},
)

EXECUTIVE_KPI_INDEX: tuple[dict, ...] = (
    {"kpi": "Revenue", "volume": "17", "api": "/api/v1/analytics/executive"},
    {"kpi": "Orders", "volume": "17", "api": "/api/v1/analytics/executive"},
    {"kpi": "Conversion", "volume": "17", "api": "/api/v1/analytics/executive"},
    {"kpi": "Forecast Accuracy", "volume": "17", "api": "/api/v1/analytics/learning"},
    {"kpi": "Campaign ROI", "volume": "17", "api": "/api/v1/dashboard/roi"},
    {"kpi": "Customer Growth", "volume": "17", "api": "/api/v1/analytics/trends"},
    {"kpi": "Segment Growth", "volume": "17", "api": "/api/v1/analytics/compare"},
    {"kpi": "Recommendation Accuracy", "volume": "17", "api": "/api/v1/analytics/recommendations"},
    {"kpi": "Learning Score", "volume": "17", "api": "/api/v1/analytics/learning"},
    {"kpi": "Le Frame Incentive", "volume": "17", "api": "/api/v1/dashboard/roi"},
)

GLOSSARY: tuple[dict, ...] = (
    {
        "term": "Customer Intelligence",
        "definition": "Generated business intelligence derived from standardized customer information.",
    },
    {
        "term": "PRIZM Proxy",
        "definition": (
            "An internal lifestyle classification approximating household characteristics "
            "using available customer and geographic information."
        ),
    },
    {
        "term": "Ceragem Segment",
        "definition": "A proprietary commercial segmentation model for Ceragem high-consideration products.",
    },
    {
        "term": "Purchase Power",
        "definition": "Estimated purchasing capability derived from multiple financial and geographic indicators.",
    },
    {
        "term": "Pain Index",
        "definition": "Estimated commercial propensity toward therapeutic wellness products.",
    },
    {
        "term": "Campaign Learning",
        "definition": "Historical campaign performance used to improve future recommendations.",
    },
    {
        "term": "Recommendation Confidence",
        "definition": "A standardized confidence score indicating the reliability of a generated recommendation.",
    },
    {
        "term": "Forecast Accuracy",
        "definition": "The degree of alignment between predicted and actual campaign outcomes.",
    },
)

VERSION_GOVERNANCE_FIELDS: tuple[str, ...] = (
    "Version",
    "Status",
    "Owner",
    "Created Date",
    "Modified Date",
    "Approval",
    "Change Log",
    "Cross Reference",
)

DOCUMENTATION_GOVERNANCE_REQUIREMENTS: tuple[str, ...] = (
    "Business Review",
    "Technical Review",
    "Architecture Review",
    "Approval",
    "Version Increment",
    "Publication",
)

MASTER_ACCEPTANCE_CRITERIA: tuple[dict, ...] = (
    {"id": "AC-01", "criterion": "Every document is indexed", "registry": "DOCUMENT_VOLUMES"},
    {"id": "AC-02", "criterion": "Every business rule is traceable", "registry": "RULES", "module": "app.rules.library"},
    {"id": "AC-03", "criterion": "Every database object is referenced", "registry": "DATABASE_CROSS_REFERENCE", "module": "app.schema.registry"},
    {"id": "AC-04", "criterion": "Every API endpoint is documented", "registry": "API_CROSS_REFERENCE", "module": "app.api.v1.router"},
    {"id": "AC-05", "criterion": "Every workflow is indexed", "registry": "WORKFLOW_CROSS_REFERENCE"},
    {"id": "AC-06", "criterion": "Every dashboard is linked to its specification", "registry": "DASHBOARD_CROSS_REFERENCE"},
    {"id": "AC-07", "criterion": "Every intelligence model has a source document", "registry": "INTELLIGENCE_CROSS_REFERENCE"},
    {"id": "AC-08", "criterion": "Every methodology references its implementation", "registry": "INTELLIGENCE_LAYERS", "module": "app.methodology.registry"},
    {"id": "AC-09", "criterion": "Documentation remains internally consistent across all volumes", "registry": "DOCUMENTATION_DEPENDENCY_MAP"},
)
