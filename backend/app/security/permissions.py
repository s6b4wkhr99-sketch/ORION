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

# (href, permission_module) — mirrors frontend ORION nav
MENU_ITEMS: tuple[tuple[str, str], ...] = (
    ("/mission-control", "dashboard"),
    ("/market-intelligence", "customer_intelligence"),
    ("/metro-intelligence", "customer_intelligence"),
    ("/opportunities", "customer_intelligence"),
    ("/customers", "customer_intelligence"),
    ("/recommendations", "campaign"),
    ("/campaigns", "campaign"),
    ("/learning", "campaign"),
    ("/admin/catalog", "settings"),
    ("/import", "upload"),
    ("/export", "export"),
    ("/buyer-import", "report_import"),
    ("/admin/users", "user_administration"),
    ("/commercial-simulator", "forecast"),
    ("/admin", "settings"),
)

MENU_HREF_TO_MODULE = dict(MENU_ITEMS)

MENU_MODULES = frozenset({
    "dashboard",
    "customer_intelligence",
    "campaign",
    "forecast",
    "upload",
    "report_import",
    "export",
    "settings",
    "user_administration",
})

IMPLIED_ACTION_MODULES: dict[str, tuple[str, ...]] = {
    "campaign": ("campaign_write", "campaign_approve"),
}


def uses_menu_hrefs(values: list[str]) -> bool:
    return bool(values) and any(str(value).startswith("/") for value in values)


def menu_hrefs_for_role(role: str) -> list[str]:
    return sorted(
        href
        for href, module in MENU_ITEMS
        if has_permission(role, module)
    )


def _modules_from_menu_hrefs(hrefs: list[str], role: str) -> set[str]:
    role_modules = set(modules_for_role(role))
    selected = {MENU_HREF_TO_MODULE[href] for href in hrefs if href in MENU_HREF_TO_MODULE}
    effective = selected & role_modules
    for menu_module, implied in IMPLIED_ACTION_MODULES.items():
        if menu_module in effective:
            effective.update(module for module in implied if module in role_modules)
    return effective


def has_permission(role: str, module: str) -> bool:
    allowed = MODULE_PERMISSIONS.get(module, frozenset())
    return role in allowed


def modules_for_role(role: str) -> list[str]:
    return sorted(module for module, roles in MODULE_PERMISSIONS.items() if role in roles)


def menu_modules_for_role(role: str) -> list[str]:
    return sorted(module for module in MENU_MODULES if has_permission(role, module))


def normalize_allowed_modules(role: str, allowed_modules: list[str] | None) -> list[str] | None:
    if allowed_modules is None:
        return None
    if uses_menu_hrefs(allowed_modules):
        role_hrefs = set(menu_hrefs_for_role(role))
        selected = sorted({href for href in allowed_modules if href in role_hrefs})
        if not selected:
            raise ValueError("At least one menu must be selected for custom access")
        return selected
    role_menu_modules = set(menu_modules_for_role(role))
    selected = sorted({module for module in allowed_modules if module in role_menu_modules})
    if not selected:
        raise ValueError("At least one menu must be selected for custom access")
    return selected


def effective_modules_for_user(role: str, allowed_modules: list[str] | None) -> list[str]:
    role_modules = set(modules_for_role(role))
    if allowed_modules is None:
        return sorted(role_modules)

    if uses_menu_hrefs(allowed_modules):
        return sorted(_modules_from_menu_hrefs(allowed_modules, role))

    effective = {module for module in allowed_modules if module in role_modules}
    for menu_module, implied in IMPLIED_ACTION_MODULES.items():
        if menu_module in effective:
            effective.update(module for module in implied if module in role_modules)
    return sorted(effective)


def has_user_module_access(role: str, allowed_modules: list[str] | None, module: str) -> bool:
    return module in effective_modules_for_user(role, allowed_modules)
