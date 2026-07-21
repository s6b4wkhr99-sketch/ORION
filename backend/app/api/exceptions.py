"""Volume 08 / Volume 24 — Standardized API error responses."""

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.error_payload import build_error_payload


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "success" in detail:
        message = detail.get("message", "Request failed")
        code = detail.get("code")
        data = detail.get("data")
    elif isinstance(detail, dict):
        message = detail.get("message") or str(detail)
        code = detail.get("code")
        data = detail
    else:
        message = str(detail)
        code = None
        data = None
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_payload(request, message, code=code, status_code=exc.status_code, data=data if data and "success" not in data else None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=build_error_payload(
            request,
            "Validation Error",
            code="VALIDATION_ERROR",
            status_code=422,
            data={"errors": exc.errors()},
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    from app.utils.audit_log import audit_error

    audit_error("api", str(exc))
    return JSONResponse(
        status_code=500,
        content=build_error_payload(request, "Internal Server Error", code="INTERNAL_ERROR", status_code=500),
    )
