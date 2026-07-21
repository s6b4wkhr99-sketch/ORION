"""Volume 11 Section 5 — Permission matrix."""

from app.security.roles import (
    ALL_ROLES,
    DATA_ADMINISTRATOR,
    EXECUTIVE_VIEWER,
    MARKETING_ANALYST,
    MARKETING_MANAGER,
    READ_ONLY,
    SYSTEM_ADMINISTRATOR,
)

MODULE_PERMISSIONS: dict[str, frozenset[str]] = {
    "dashboard": ALL_ROLES,
    "upload": frozenset({SYSTEM_ADMINISTRATOR, DATA_ADMINISTRATOR}),
    "customer_intelligence": ALL_ROLES,
    "campaign": frozenset({
        SYSTEM_ADMINISTRATOR,
        MARKETING_MANAGER,
        MARKETING_ANALYST,
        EXECUTIVE_VIEWER,
    }),
    "campaign_write": frozenset({SYSTEM_ADMINISTRATOR, MARKETING_MANAGER}),
    "campaign_approve": frozenset({SYSTEM_ADMINISTRATOR, MARKETING_MANAGER}),
    "forecast": frozenset({
        SYSTEM_ADMINISTRATOR,
        MARKETING_MANAGER,
        MARKETING_ANALYST,
        EXECUTIVE_VIEWER,
        READ_ONLY,
    }),
    "export": frozenset({SYSTEM_ADMINISTRATOR, MARKETING_MANAGER}),
    "report_import": frozenset({
        SYSTEM_ADMINISTRATOR,
        MARKETING_MANAGER,
        MARKETING_ANALYST,
        DATA_ADMINISTRATOR,
    }),
    "rule_library": frozenset({SYSTEM_ADMINISTRATOR}),
    "settings": frozenset({SYSTEM_ADMINISTRATOR}),
    "user_administration": frozenset({SYSTEM_ADMINISTRATOR}),
}


def has_permission(role: str, module: str) -> bool:
    allowed = MODULE_PERMISSIONS.get(module, frozenset())
    return role in allowed
