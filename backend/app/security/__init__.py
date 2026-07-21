"""Volume 11 — Security module."""

from app.security.audit import list_audit_logs, record_audit
from app.security.password import PasswordPolicyError, hash_password, validate_password_policy, verify_password
from app.security.permissions import MODULE_PERMISSIONS, has_permission
from app.security.roles import ALL_ROLES, SYSTEM_ADMINISTRATOR

__all__ = [
    "ALL_ROLES",
    "SYSTEM_ADMINISTRATOR",
    "MODULE_PERMISSIONS",
    "has_permission",
    "hash_password",
    "verify_password",
    "validate_password_policy",
    "PasswordPolicyError",
    "record_audit",
    "list_audit_logs",
]
