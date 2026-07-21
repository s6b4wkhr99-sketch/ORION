import logging
import threading

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from app.api.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.api.responses import ok
from app.devops.health import build_health_payload, health_http_status
from app.devops.logging_config import configure_logging
from app.devops.middleware import RequestLoggingMiddleware
from app.devops.security_headers import SecurityHeadersMiddleware
from app.security.rate_limit import rate_limiter
from app.api.router import router as legacy_router
from app.api.v1.router import router as v1_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import *  # noqa: F401, F403
from app.processing.seed import seed_configuration
from app.security.users import seed_users

configure_logging()
logger = logging.getLogger("cios.main")

app = FastAPI(
    title="Ceragem CIOS",
    description="Customer Intelligence Operating System — Enterprise Campaign Decision Platform",
    version=settings.app_version,
    debug=settings.debug,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
# Compress large JSON payloads (e.g. multi-MB ZCTA choropleth GeoJSON) ~5-10x over the wire.
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    if not settings.rate_limit_enabled:
        return await call_next(request)
    path = request.url.path
    if path in ("/health", "/api/v1/health") or path.startswith("/api/v1/health"):
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    if path.startswith("/api/"):
        rate_limiter.check(request)
    return await call_next(request)


app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

app.include_router(v1_router, prefix="/api")
app.include_router(legacy_router, prefix="/api")


@app.on_event("startup")
def on_startup():
    logger.info(
        "Starting CIOS environment=%s version=%s",
        settings.environment,
        settings.app_version,
    )
    Base.metadata.create_all(bind=engine)
    if not settings.skip_physical_schema:
        from app.schema.apply import apply_physical_schema

        apply_physical_schema(engine)
    db = SessionLocal()
    try:
        if not settings.skip_startup_seed:
            from app.schema.seed_v16 import seed_v16_reference_schema

            seed_configuration(db)
            seed_users(db)
            seed_v16_reference_schema(db)
        from app.commercial.catalog import warm_catalog_cache
        from app.campaign.executive_dashboard import get_executive_summary

        if settings.dashboard_cache_invalidate_on_startup:
            from app.cache.dashboard_cache import invalidate_dashboard_cache

            invalidate_dashboard_cache()
        warm_catalog_cache(db)

        def _warm_executive_dashboard_cache() -> None:
            warm_db = SessionLocal()
            try:
                get_executive_summary(warm_db, None)
                logger.info("Executive dashboard cache warmed")
            except Exception:
                logger.exception("Executive dashboard cache warm failed")
            finally:
                warm_db.close()

        # Warm in background so /health and uploads respond while post-rescore rollups rebuild.
        threading.Thread(
            target=_warm_executive_dashboard_cache,
            daemon=True,
            name="executive-dashboard-cache-warm",
        ).start()
    finally:
        db.close()


@app.get("/health")
def health_legacy():
    """Legacy load-balancer probe (kept for backward compatibility)."""
    payload = build_health_payload()
    return {"status": "ok" if health_http_status(payload) == 200 else "degraded", "service": "ceragem-cios", "version": settings.app_version}


@app.get("/api/v1/health")
def health_v1():
    """Volume 13 Section 11 — Application, database, and storage health."""
    payload = build_health_payload()
    status = health_http_status(payload)
    return JSONResponse(status_code=status, content=ok(payload))
