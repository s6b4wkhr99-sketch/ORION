"""Volume 13 Section 11 — Health check probes."""

from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import engine, is_postgres_url
from app.acquisition.upload_profile import get_upload_processing_profile
from app.utils.timezone import app_timezone_label, now_app_iso


def _check_database() -> dict[str, Any]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "up", "driver": engine.url.get_driver_name()}
    except SQLAlchemyError as exc:
        return {"status": "down", "error": str(exc)}


def _check_storage() -> dict[str, Any]:
    paths = {
        "upload": Path(settings.upload_dir),
        "export": Path(settings.export_path),
    }
    results: dict[str, Any] = {}
    all_ok = True
    for name, path in paths.items():
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".health_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            results[name] = {"status": "up", "path": str(path.resolve())}
        except OSError as exc:
            all_ok = False
            results[name] = {"status": "down", "path": str(path), "error": str(exc)}
    return {"status": "up" if all_ok else "down", "paths": results}


def build_health_payload() -> dict[str, Any]:
    db = _check_database()
    storage = _check_storage()
    app_ok = db["status"] == "up" and storage["status"] == "up"
    upload_profile = get_upload_processing_profile(settings.bulk_upload_row_threshold)
    return {
        "application": {"status": "up" if app_ok else "degraded", "environment": settings.environment},
        "database": {
            **db,
            "postgres": is_postgres_url(),
            "url_scheme": engine.url.get_driver_name(),
        },
        "storage": storage,
        "upload_pipeline": {
            "async": upload_profile["upload_async"],
            "bulk_mode": upload_profile["bulk_upload_mode"],
            "customer_analysis_only": upload_profile["customer_analysis_only"],
            "ready_for_2_5m": is_postgres_url() and upload_profile["upload_async"],
        },
        "version": settings.app_version,
        "timestamp": now_app_iso(),
        "timezone": {
            "id": settings.app_timezone,
            "label": app_timezone_label(),
        },
    }


def health_http_status(payload: dict[str, Any]) -> int:
    app = payload.get("application", {})
    db = payload.get("database", {})
    storage = payload.get("storage", {})
    if app.get("status") == "up" and db.get("status") == "up" and storage.get("status") == "up":
        return 200
    return 503
