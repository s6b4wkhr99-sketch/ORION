"""Volume 11 Section 4 — System roles."""

SYSTEM_ADMINISTRATOR = "System Administrator"
MARKETING_MANAGER = "Marketing Manager"
MARKETING_ANALYST = "Marketing Analyst"
DATA_ADMINISTRATOR = "Data Administrator"
EXECUTIVE_VIEWER = "Executive Viewer"
READ_ONLY = "Read Only"

ALL_ROLES: frozenset[str] = frozenset({
    SYSTEM_ADMINISTRATOR,
    MARKETING_MANAGER,
    MARKETING_ANALYST,
    DATA_ADMINISTRATOR,
    EXECUTIVE_VIEWER,
    READ_ONLY,
})

# Legacy alias
ADMINISTRATOR = SYSTEM_ADMINISTRATOR
