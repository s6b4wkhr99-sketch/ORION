"""Volume 07 / 11 — API dependencies, RBAC, and request context."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.auth import decode_token
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.security.permissions import has_permission, has_user_module_access
from app.security.roles import ALL_ROLES, SYSTEM_ADMINISTRATOR

_bearer = HTTPBearer(auto_error=False)


def get_client_meta(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "browser": request.headers.get("user-agent"),
    }


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    meta = get_client_meta(request)

    if credentials and credentials.scheme.lower() == "bearer":
        try:
            payload = decode_token(credentials.credentials)
            email = payload.get("sub")
            role = payload.get("role", SYSTEM_ADMINISTRATOR)
            if not email:
                raise HTTPException(status_code=401, detail={"success": False, "message": "Invalid token"})
            request.state.user_email = email
            return {"email": email, "role": role, "name": email.split("@")[0], **meta}
        except HTTPException:
            raise
        except Exception as exc:
            if settings.auth_required:
                raise HTTPException(
                    status_code=401,
                    detail={"success": False, "message": "Invalid or expired token"},
                ) from exc

    if credentials and credentials.scheme.lower() == "bearer" and not settings.auth_required:
        # Invalid token path fell through — use dev identity.
        request.state.user_email = settings.auth_user_email
        return {
            "email": settings.auth_user_email,
            "role": SYSTEM_ADMINISTRATOR,
            "name": "CIOS Admin",
            **meta,
        }

    if not settings.auth_required:
        request.state.user_email = settings.auth_user_email
        return {
            "email": settings.auth_user_email,
            "role": SYSTEM_ADMINISTRATOR,
            "name": "CIOS Admin",
            **meta,
        }

    raise HTTPException(
        status_code=401,
        detail={"success": False, "message": "Unauthorized — Bearer token required"},
    )


def require_module(module: str) -> Callable:
    def checker(user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
        row = db.query(User).filter(User.email == user.get("email")).first()
        role = user.get("role", "")
        allowed_modules = row.allowed_modules if row else None
        if allowed_modules is not None:
            if not has_user_module_access(role, allowed_modules, module):
                raise HTTPException(
                    status_code=403,
                    detail={"success": False, "message": f"Forbidden — insufficient permission for {module}"},
                )
        elif not has_permission(role, module):
            raise HTTPException(
                status_code=403,
                detail={"success": False, "message": f"Forbidden — insufficient permission for {module}"},
            )
        return user

    return checker


require_dashboard = require_module("dashboard")
require_upload = require_module("upload")
require_customer_intelligence = require_module("customer_intelligence")
require_campaign = require_module("campaign")
require_campaign_write = require_module("campaign_write")
require_campaign_approve = require_module("campaign_approve")
require_forecast = require_module("forecast")
require_export = require_module("export")
require_report_import = require_module("report_import")
require_settings = require_module("settings")
require_user_admin = require_module("user_administration")
require_rule_library = require_module("rule_library")
