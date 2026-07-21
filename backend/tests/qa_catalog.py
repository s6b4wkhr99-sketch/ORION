"""Volume 12 — Test case catalog (spec traceability)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TestCase:
    test_id: str
    name: str
    category: str
    spec_section: str


CATALOG: tuple[TestCase, ...] = (
    # Section 5 — Upload
    TestCase("TEST-UP-001", "Upload Excel", "Integration", "§5"),
    TestCase("TEST-UP-002", "Upload CSV", "Integration", "§5"),
    TestCase("TEST-UP-003", "Duplicate Customer", "Integration", "§5"),
    TestCase("TEST-UP-004", "Invalid Email", "Integration", "§5"),
    TestCase("TEST-UP-005", "Invalid ZIP", "Integration", "§5"),
    # Section 6 — Mapping
    TestCase("TEST-MAP-001", "Verify Field Mapping", "Integration", "§6"),
    TestCase("TEST-MAP-002", "Manual Mapping Preview", "Integration", "§6"),
    TestCase("TEST-MAP-003", "Unknown Column", "Integration", "§6"),
    # Section 7 — Datalogix
    TestCase("TEST-DAT-001", "Original Value Preservation X", "Unit", "§7"),
    TestCase("TEST-DAT-002", "No Numeric Conversion Z", "Unit", "§7"),
    TestCase("TEST-DAT-003", "Income Interpretation", "Unit", "§7"),
    # Section 8 — Intelligence
    TestCase("TEST-INT-001", "PRIZM Proxy Generation", "Intelligence", "§8"),
    TestCase("TEST-INT-002", "Ceragem Segment", "Intelligence", "§8"),
    TestCase("TEST-INT-003", "Purchase Power Levels", "Intelligence", "§8"),
    TestCase("TEST-INT-004", "Pain Index", "Intelligence", "§8"),
    TestCase("TEST-INT-005", "Lifestyle", "Intelligence", "§8"),
    TestCase("TEST-INT-006", "Recommendation", "Intelligence", "§8"),
    # Section 9 — Campaign
    TestCase("TEST-CAM-001", "Create Campaign", "Integration", "§9"),
    TestCase("TEST-CAM-002", "Forecast", "Integration", "§9"),
    TestCase("TEST-CAM-003", "Approval", "Integration", "§9"),
    TestCase("TEST-CAM-004", "Export", "Integration", "§9"),
    TestCase("TEST-CAM-005", "Import Campaign Report", "Integration", "§9"),
    # Section 10 — Dashboard
    TestCase("TEST-DB-001", "Executive Dashboard", "API", "§10"),
    TestCase("TEST-DB-002", "Customer Dashboard", "API", "§10"),
    TestCase("TEST-DB-003", "State Dashboard", "API", "§10"),
    TestCase("TEST-DB-004", "ZIP Dashboard", "API", "§10"),
    TestCase("TEST-DB-005", "ROI Dashboard", "API", "§10"),
    # Section 11 — API
    TestCase("TEST-API-001", "Authentication", "API", "§11"),
    TestCase("TEST-API-002", "Customer Upload API", "API", "§11"),
    TestCase("TEST-API-003", "Forecast API", "API", "§11"),
    TestCase("TEST-API-004", "Export API", "API", "§11"),
    TestCase("TEST-API-005", "Dashboard API", "API", "§11"),
    # Section 12 — Security
    TestCase("TEST-SEC-001", "Unauthorized Access", "Security", "§12"),
    TestCase("TEST-SEC-002", "Insufficient Permission", "Security", "§12"),
    TestCase("TEST-SEC-003", "Expired Token", "Security", "§12"),
    TestCase("TEST-SEC-004", "SQL Injection", "Security", "§12"),
    TestCase("TEST-SEC-005", "XSS Attempt", "Security", "§12"),
    # Section 13 — Performance
    TestCase("TEST-PERF-001", "Upload Performance", "Performance", "§13"),
    TestCase("TEST-PERF-002", "Dashboard Performance", "Performance", "§13"),
    TestCase("TEST-PERF-003", "Forecast Performance", "Performance", "§13"),
    TestCase("TEST-PERF-004", "Export Performance", "Performance", "§13"),
    TestCase("TEST-PERF-005", "Concurrent Requests", "Performance", "§13"),
    # Section 14 — Regression marker
    TestCase("TEST-REG-001", "Regression Suite", "Regression", "§14"),
)

CATALOG_BY_ID = {t.test_id: t for t in CATALOG}
