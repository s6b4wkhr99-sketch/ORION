"""Volume 24 — Standardized API error payload helpers."""

from __future__ import annotations

from starlette.requests import Request

from app.utils.timezone import now_app_iso


def error_code_for_status(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
    }
    return mapping.get(status_code, "REQUEST_FAILED")


def build_error_payload(
    request: Request | None,
    message: str,
    *,
    code: str | None = None,
    status_code: int = 400,
    data: dict | None = None,
) -> dict:
    """Volume 24 §11–12 — standardized error envelope with backward-compatible message."""
    resolved_code = code or error_code_for_status(status_code)
    request_id = None
    if request is not None:
        request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

    payload: dict = {
        "success": False,
        "message": message,
        "error": {
            "code": resolved_code,
            "message": message,
            "timestamp": now_app_iso(),
            "requestId": request_id,
        },
    }
    if data:
        payload["data"] = data
    return payload
