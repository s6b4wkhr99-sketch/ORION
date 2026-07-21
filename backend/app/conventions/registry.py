"""Volume 24 — Development Convention registry (SSOT)."""

CONVENTION_VERSION = "Volume 24 v1.0"
CONVENTION_STATUS = "Final"
CONVENTION_OWNER = "Ceragem CIOS Engineering"

GENERAL_PRINCIPLES: tuple[str, ...] = (
    "Readable",
    "Predictable",
    "Modular",
    "Testable",
    "Documented",
    "Metadata Driven",
)

ARCHITECTURE_LAYERS: tuple[str, ...] = (
    "Presentation Layer",
    "Application Layer",
    "Business Layer",
    "Intelligence Layer",
    "Repository Layer",
    "Database",
)

FRONTEND_FOLDERS: tuple[str, ...] = (
    "app/",
    "components/",
    "layouts/",
    "hooks/",
    "services/",
    "stores/",
    "types/",
    "utils/",
    "styles/",
)

BACKEND_FOLDERS: tuple[str, ...] = (
    "api/",
    "models/",
    "schemas/",
    "services/",
    "repositories/",
    "intelligence/",
    "campaign/",
    "forecast/",
    "mapping/",
    "providers/",
    "dashboard/",
    "middleware/",
    "utils/",
)

FILE_NAMING = "kebab-case"
CLASS_NAMING = "PascalCase"
PYTHON_FUNCTION_NAMING = "camelCase (public service methods) / snake_case (internal modules)"
TYPESCRIPT_FUNCTION_NAMING = "camelCase"
PYTHON_VARIABLE_NAMING = "snake_case"
TYPESCRIPT_VARIABLE_NAMING = "camelCase"

DATABASE_CONVENTIONS: dict[str, str] = {
    "tables": "snake_case",
    "columns": "snake_case",
    "primary_keys": "table_name_id or id",
    "foreign_keys": "referenced_table_id",
    "indexes": "idx_table_column",
    "views": "vw_name",
    "materialized_views": "mv_name",
}

API_EXAMPLES: tuple[str, ...] = (
    "GET /api/v1/customers",
    "POST /api/v1/customers/upload",
    "GET /api/v1/dashboard",
    "POST /api/v1/campaign",
    "POST /api/v1/export",
    "POST /api/v1/campaigns/report/upload",
)

BUSINESS_RULE_FLOW: tuple[str, ...] = (
    "Controller",
    "Service",
    "Business Rule",
    "Repository",
)

IMMUTABLE_INTELLIGENCE_FIELDS: tuple[str, ...] = (
    "purchase_power",
    "pain_index",
    "lifestyle",
    "prizm_proxy",
    "ceragem_segment",
    "recommendation",
)

UPLOAD_WORKFLOW: tuple[str, ...] = (
    "Upload",
    "Header Detection",
    "Alias Mapping",
    "Standardization",
    "Validation",
    "Import",
    "Customer Intelligence",
)

UI_PAGE_SECTIONS: tuple[str, ...] = (
    "Header",
    "Breadcrumb",
    "Global Filter",
    "Main Content",
    "Action Panel",
    "Status Indicator",
    "Footer",
)

DASHBOARD_CAPABILITIES: tuple[str, ...] = (
    "Global Search",
    "Sorting",
    "Filtering",
    "Pagination",
    "Export",
    "Drill-down",
    "Responsive Layout",
)

LOG_SEVERITY_LEVELS: tuple[str, ...] = ("INFO", "WARNING", "ERROR", "CRITICAL")

LOG_FIELDS: tuple[str, ...] = (
    "timestamp",
    "request_id",
    "module",
    "user_id",
    "execution_ms",
    "severity",
    "message",
)

ERROR_FIELDS: tuple[str, ...] = ("code", "message", "timestamp", "requestId")

CONFIGURATION_SOURCES: tuple[str, ...] = (
    "Environment Variables",
    "Reference Tables",
    "Metadata Repository",
)

TEST_TYPES: tuple[str, ...] = (
    "Unit Test",
    "Integration Test",
    "Regression Test",
    "Business Validation",
)

GIT_COMMIT_FORMAT = "type(scope): description"

GIT_COMMIT_EXAMPLES: tuple[str, ...] = (
    "feat(upload): add auto mapping engine",
    "fix(api): correct dashboard response",
    "refactor(engine): simplify recommendation logic",
    "docs(metadata): update field dictionary",
    "test(campaign): add forecast unit tests",
)

PROHIBITED_PRACTICES: tuple[str, ...] = (
    "Hard-coded business rules",
    "Hard-coded provider mappings",
    "Duplicate logic",
    "Direct SQL inside controllers",
    "Manual Intelligence updates",
    "Magic numbers",
    "Anonymous business logic",
    "Inconsistent response formats",
)

CODE_REVIEW_CHECKLIST: tuple[str, ...] = (
    "Naming conventions followed",
    "Tests pass",
    "Documentation updated",
    "Metadata updated",
    "Business Rules unchanged",
    "No hard-coded values",
    "API format verified",
    "Logging implemented",
    "Error handling verified",
)

CONVENTION_ACCEPTANCE_CRITERIA: tuple[dict, ...] = (
    {"id": "CONV-01", "criterion": "All developers follow the same naming standards"},
    {"id": "CONV-02", "criterion": "Business logic remains centralized"},
    {"id": "CONV-03", "criterion": "APIs return standardized responses"},
    {"id": "CONV-04", "criterion": "Metadata drives configuration"},
    {"id": "CONV-05", "criterion": "Intelligence remains immutable"},
    {"id": "CONV-06", "criterion": "Code is modular and testable"},
    {"id": "CONV-07", "criterion": "Logging and error handling are consistent"},
    {"id": "CONV-08", "criterion": "Cursor-generated code follows the same conventions"},
)

# Runtime module mapping (actual CIOS layout vs Volume 24 target folders)
BACKEND_MODULE_MAP: tuple[dict, ...] = (
    {"convention": "api/", "path": "app/api/", "volume": "07"},
    {"convention": "models/", "path": "app/models/", "volume": "16"},
    {"convention": "schemas/", "path": "app/schemas/", "volume": "07"},
    {"convention": "services/", "path": "app/api/services/", "volume": "07"},
    {"convention": "intelligence/", "path": "app/intelligence/", "volume": "04"},
    {"convention": "campaign/", "path": "app/campaign/", "volume": "06"},
    {"convention": "forecast/", "path": "app/intelligence/forecasting.py", "volume": "04"},
    {"convention": "mapping/", "path": "app/mapping/", "volume": "09"},
    {"convention": "providers/", "path": "app/providers/", "volume": "15"},
    {"convention": "dashboard/", "path": "app/campaign/dashboards.py", "volume": "05"},
    {"convention": "middleware/", "path": "app/devops/middleware.py", "volume": "13"},
    {"convention": "utils/", "path": "app/utils/", "volume": "08"},
)

FRONTEND_MODULE_MAP: tuple[dict, ...] = (
    {"convention": "app/", "path": "frontend/src/app/"},
    {"convention": "components/", "path": "frontend/src/components/"},
    {"convention": "layouts/", "path": "frontend/src/components/layout/"},
    {"convention": "utils/", "path": "frontend/src/lib/"},
    {"convention": "types/", "path": "frontend/src/lib/api.ts"},
)
