"""Volume 14 Section 3 — System Administrator dashboard aggregates."""

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.config import settings
from app.devops.health import build_health_payload
from app.models.audit import AuditLog
from app.models.campaign import Campaign
from app.models.raw import RawUpload
from app.operations.metrics_store import operational_metrics

RUNNING_CAMPAIGN_STATUSES = frozenset({"draft", "forecast", "approved", "active", "running"})
UPLOAD_QUEUE_STATUSES = frozenset({"pending", "processing"})


def _system_resources() -> dict:
    cpu_percent: float | None = None
    memory_percent: float | None = None
    try:
        import psutil

        cpu_percent = round(psutil.cpu_percent(interval=0.1), 1)
        memory_percent = round(psutil.virtual_memory().percent, 1)
    except ImportError:
        load = os.getloadavg()[0] if hasattr(os, "getloadavg") else None
        cpu_percent = round(load * 100, 1) if load is not None else None

    upload_path = Path(settings.upload_dir)
    backup_path = Path(settings.backup_path)
    disk = shutil.disk_usage(upload_path if upload_path.exists() else Path("."))
    storage_used_mb = round((disk.total - disk.free) / (1024 * 1024), 1)
    storage_total_mb = round(disk.total / (1024 * 1024), 1)
    storage_percent = round((disk.used / disk.total) * 100, 1) if disk.total else 0

    return {
        "cpuUsagePercent": cpu_percent,
        "memoryUsagePercent": memory_percent,
        "storageUsedMb": storage_used_mb,
        "storageTotalMb": storage_total_mb,
        "storageUsagePercent": storage_percent,
    }


def _latest_backup() -> dict:
    backup_root = Path(settings.backup_path)
    if not backup_root.exists():
        return {"status": "missing", "path": str(backup_root.resolve())}
    dirs = sorted([p for p in backup_root.iterdir() if p.is_dir()], reverse=True)
    if not dirs:
        return {"status": "empty", "path": str(backup_root.resolve())}
    latest = dirs[0]
    mtime = datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600
    return {
        "status": "ok" if age_hours < 26 else "stale",
        "path": str(latest),
        "completedAt": mtime.isoformat(),
        "ageHours": round(age_hours, 1),
    }


def _notifications(db: Session) -> list[dict]:
    alerts: list[dict] = []
    health = build_health_payload()
    if health["application"]["status"] != "up":
        alerts.append({"severity": "critical", "message": "Application degraded", "module": "system"})
    if health["database"]["status"] != "up":
        alerts.append({"severity": "critical", "message": "Database unavailable", "module": "database"})
    if health["storage"]["status"] != "up":
        alerts.append({"severity": "high", "message": "Storage probe failed", "module": "storage"})

    backup = _latest_backup()
    if backup["status"] in {"missing", "empty", "stale"}:
        alerts.append({"severity": "high", "message": f"Backup {backup['status']}", "module": "backup"})

    failed_auth = (
        db.query(func.count(AuditLog.audit_id))
        .filter(AuditLog.action == "login_failed", AuditLog.timestamp >= datetime.utcnow().replace(hour=0, minute=0))
        .scalar()
        or 0
    )
    if failed_auth > 5:
        alerts.append({"severity": "medium", "message": f"{failed_auth} failed logins today", "module": "auth"})

    pending_uploads = (
        db.query(func.count(RawUpload.upload_id))
        .filter(RawUpload.status.in_(UPLOAD_QUEUE_STATUSES))
        .scalar()
        or 0
    )
    if pending_uploads > 0:
        alerts.append({"severity": "low", "message": f"{pending_uploads} uploads in queue", "module": "upload"})

    return alerts


def get_admin_dashboard(db: Session) -> dict:
    health = build_health_payload()
    resources = _system_resources()
    backup = _latest_backup()

    upload_queue = [
        {
            "uploadId": str(u.upload_id),
            "fileName": u.filename,
            "status": u.status,
            "createdAt": u.uploaded_date.isoformat() if u.uploaded_date else None,
        }
        for u in db.query(RawUpload)
        .filter(RawUpload.status.in_(UPLOAD_QUEUE_STATUSES))
        .order_by(RawUpload.uploaded_date.desc())
        .limit(20)
        .all()
    ]

    running_campaigns = [
        {
            "campaignId": c.campaign_id,
            "campaignName": c.campaign_name,
            "status": c.status,
            "provider": c.provider,
        }
        for c in db.query(Campaign)
        .filter(Campaign.status.in_(RUNNING_CAMPAIGN_STATUSES))
        .order_by(Campaign.created_at.desc())
        .limit(20)
        .all()
    ]

    db_ping_ms: float | None = None
    try:
        started = datetime.now(timezone.utc)
        db.execute(text("SELECT 1"))
        db_ping_ms = round((datetime.now(timezone.utc) - started).total_seconds() * 1000, 2)
    except Exception:
        db_ping_ms = None

    critical_alerts = [n for n in _notifications(db) if n["severity"] in {"critical", "high"}]

    return {
        "systemStatus": health["application"]["status"],
        "environment": settings.environment,
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpuUsagePercent": resources["cpuUsagePercent"],
        "memoryUsagePercent": resources["memoryUsagePercent"],
        "databaseStatus": health["database"],
        "databasePingMs": db_ping_ms,
        "storageUsage": {
            **resources,
            "uploadPath": str(Path(settings.upload_dir).resolve()),
            "exportPath": str(Path(settings.export_path).resolve()),
            "probeStatus": health["storage"]["status"],
        },
        "apiHealth": {
            "status": "up" if health["application"]["status"] == "up" else "degraded",
            "version": health["version"],
        },
        "runningCampaigns": running_campaigns,
        "uploadQueue": upload_queue,
        "scheduledJobs": [
            {"name": "daily_backup", "schedule": "02:00 UTC", "status": backup["status"]},
            {"name": "worker_heartbeat", "schedule": f"every {os.getenv('WORKER_POLL_SECONDS', '30')}s", "status": "active"},
        ],
        "backup": backup,
        "notificationCenter": _notifications(db),
        "criticalAlertCount": len(critical_alerts),
        "operationalMetrics": operational_metrics(),
    }
