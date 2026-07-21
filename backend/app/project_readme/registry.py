"""Volume 23 — Project README registry (canonical README content)."""

README_VERSION = "Volume 23 v1.0"
README_STATUS = "Final"
README_OWNER = "Ceragem CIOS"

PLATFORM_NAME = "Ceragem Customer Intelligence Operating System (CIOS)"

PLATFORM_DEFINITION = (
    "CIOS is an enterprise customer intelligence platform designed to transform "
    "uploaded customer data into actionable campaign intelligence."
)

WHAT_CIOS_IS_NOT: tuple[str, ...] = (
    "CIOS is not a CRM.",
    "CIOS is not a Mass Email Provider.",
)

WHAT_CIOS_IS = (
    "CIOS is a Customer Intelligence Operating System that connects customer data, "
    "Datalogix intelligence, ZIP intelligence, PRIZM Proxy segmentation, Ceragem commercial "
    "segmentation, campaign forecasting, provider export, campaign report import, and "
    "executive analytics into one operating platform."
)

BUSINESS_QUESTIONS: tuple[str, ...] = (
    "Which customers are most likely to purchase?",
    "Which State should be prioritized?",
    "Which ZIP has the highest opportunity?",
    "Which Ceragem product should be recommended?",
    "Which message direction should be used?",
    "What is the expected conversion?",
    "What is the expected revenue?",
    "What is the expected Le Frame incentive?",
    "Which campaign should be executed next?",
)

CORE_WORKFLOW: tuple[str, ...] = (
    "Excel / CSV Upload",
    "Auto Mapping Engine",
    "Data Standardization",
    "Validation",
    "Customer Database",
    "Datalogix Intelligence",
    "ZIP Intelligence",
    "PRIZM Proxy Segment",
    "Ceragem Segment",
    "Message Direction",
    "Recommendation Engine",
    "Revenue Forecast",
    "Dashboard",
    "Provider Export",
    "Campaign Execution",
    "Campaign Report Import",
    "Learning Database",
)

REPOSITORY_STRUCTURE: tuple[dict, ...] = (
    {"path": "frontend/", "description": "Next.js, React, TypeScript, Tailwind, Recharts"},
    {"path": "backend/", "description": "FastAPI, SQLAlchemy, Pandas"},
    {"path": "docs/", "description": "Approved specifications (Volumes 01–23)"},
    {"path": "spec/", "description": "Pointer to docs/"},
    {"path": "sample_data/", "description": "CSV samples for upload and campaign reports"},
)

DEFAULT_LOGIN = {"email": "user@company.com", "password": "Ceragem2026!Adm", "role": "System Administrator"}

API_BASE = "/api/v1"

README_ACCEPTANCE_CRITERIA: tuple[dict, ...] = (
    {"id": "README-01", "criterion": "Project overview defines CIOS purpose"},
    {"id": "README-02", "criterion": "Core business questions are documented"},
    {"id": "README-03", "criterion": "End-to-end workflow is documented"},
    {"id": "README-04", "criterion": "Repository structure is documented"},
    {"id": "README-05", "criterion": "Quick start instructions are present"},
    {"id": "README-06", "criterion": "Documentation library is indexed"},
)
