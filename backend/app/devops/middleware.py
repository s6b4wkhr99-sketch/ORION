"""Volume 13 Section 12 — Request logging with trace context."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.operations.metrics_store import record_timing

logger = logging.getLogger("cios.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            user_id = getattr(request.state, "user_email", None) or "-"
            status = response.status_code if response else 500
            extra = {
                "request_id": request_id,
                "user_id": user_id,
                "cios_module": request.url.path.split("/")[2] if request.url.path.startswith("/api/") else "app",
                "execution_ms": elapsed_ms,
            }
            logger.info(
                "%s %s status=%s",
                request.method,
                request.url.path,
                status,
                extra=extra,
            )
            if request.url.path.startswith("/api/v1/"):
                category = "api"
                if "/dashboard" in request.url.path:
                    category = "dashboard"
                elif "/customers/upload" in request.url.path:
                    category = "upload"
                elif "/forecast" in request.url.path:
                    category = "forecast"
                elif "/export" in request.url.path:
                    category = "export"
                elif "/report/upload" in request.url.path:
                    category = "import"
                elif "/campaign" in request.url.path:
                    category = "campaign"
                record_timing(category, elapsed_ms)
            if response:
                response.headers["X-Request-Id"] = request_id
