"""Volume 28.1 Phase C — database and storage maintenance."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine
from app.models.audit import AuditLog
from app.models.export import ExportJob
from app.models.raw import RawCustomerData, RawUpload
from app.schema.apply import refresh_materialized_views
from app.schema.views import MATERIALIZED_VIEW_DDL

logger = logging.getLogger("cios.ops")

REINDEX_TABLES = (
    "customers",
    "customer_intelligence",
    "upload_rollup",
    "audit_log",
)


def is_postgres() -> bool:
    dialect = engine.url.get_driver_name()
    return dialect.startswith("postgresql") or dialect.startswith("psycopg2")


def refresh_materialized_views_job() -> list[str]:
    if not is_postgres():
        logger.info("mv_refresh_skipped reason=not_postgres")
        return []
    refresh_materialized_views(engine)
    names = list(MATERIALIZED_VIEW_DDL.keys())
    logger.info("mv_refresh_complete views=%s", ",".join(names))
    return names


def vacuum_analyze_job() -> bool:
    if not is_postgres():
        logger.info("vacuum_skipped reason=not_postgres")
        return False
    tables = (
        "customers",
        "customer_intelligence",
        "upload_rollup",
        "raw_upload",
        "export_job",
        "audit_log",
    )
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for table in tables:
            conn.execute(text(f"VACUUM ANALYZE {table}"))
    logger.info("vacuum_analyze_complete tables=%s", ",".join(tables))
    return True


def reindex_tables_job() -> list[str]:
    if not is_postgres():
        logger.info("reindex_skipped reason=not_postgres")
        return []
    completed: list[str] = []
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for table in REINDEX_TABLES:
            try:
                conn.execute(text(f"REINDEX TABLE {table}"))
                completed.append(table)
            except Exception as exc:
                logger.warning("reindex_failed table=%s error=%s", table, exc)
    logger.info("reindex_complete tables=%s", ",".join(completed))
    return completed


def _unlink(path: str | None) -> bool:
    if not path or not os.path.isfile(path):
        return False
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def cleanup_exports(db: Session) -> tuple[int, int]:
    cutoff = datetime.utcnow() - timedelta(days=settings.export_retention_days)
    jobs = db.query(ExportJob).filter(ExportJob.created_at < cutoff).all()
    removed_files = 0
    removed_jobs = 0
    for job in jobs:
        if _unlink(job.download_url):
            removed_files += 1
        db.delete(job)
        removed_jobs += 1
    if removed_jobs:
        db.commit()
    return removed_jobs, removed_files


def cleanup_temp_directories() -> int:
    cutoff = datetime.utcnow() - timedelta(hours=settings.temp_retention_hours)
    removed = 0
    directories = [
        Path("/tmp/uploads"),
        Path("/tmp/export"),
        Path("/tmp/report"),
    ]
    for directory in directories:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            mtime = datetime.utcfromtimestamp(path.stat().st_mtime)
            if mtime < cutoff:
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    continue
    return removed


def cleanup_old_upload_archives() -> int:
    cutoff = datetime.utcnow() - timedelta(days=settings.upload_archive_retention_days)
    removed = 0
    upload_root = Path(settings.upload_dir)
    if not upload_root.exists():
        return 0
    for path in upload_root.rglob("*.gz"):
        mtime = datetime.utcfromtimestamp(path.stat().st_mtime)
        if mtime < cutoff:
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue
    return removed


def archive_audit_logs(db: Session) -> int:
    """Move audit rows older than retention window into audit_log_archive."""
    if not is_postgres():
        return 0
    cutoff = datetime.utcnow() - timedelta(days=settings.audit_log_retention_days)
    old_rows = db.query(AuditLog).filter(AuditLog.timestamp < cutoff).limit(5000).all()
    if not old_rows:
        return 0

    archived = 0
    for row in old_rows:
        db.execute(
            text(
                """
                INSERT INTO audit_log_archive (
                    audit_id, timestamp, user_id, role, action, entity_type, entity_id,
                    before_value, after_value, ip_address, browser, status, duration_ms, archived_at
                )
                VALUES (
                    :audit_id, :timestamp, :user_id, :role, :action, :entity_type, :entity_id,
                    :before_value, :after_value, :ip_address, :browser, :status, :duration_ms, :archived_at
                )
                ON CONFLICT (audit_id) DO NOTHING
                """
            ),
            {
                "audit_id": row.audit_id,
                "timestamp": row.timestamp,
                "user_id": row.user_id,
                "role": row.role,
                "action": row.action,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "before_value": row.before_value,
                "after_value": row.after_value,
                "ip_address": row.ip_address,
                "browser": row.browser,
                "status": row.status,
                "duration_ms": row.duration_ms,
                "archived_at": datetime.utcnow(),
            },
        )
        db.delete(row)
        archived += 1
    db.commit()
    logger.info("audit_archive_complete archived=%s cutoff=%s", archived, cutoff.isoformat())
    return archived


def build_storage_audit(db: Session) -> dict:
    upload_dir = Path(settings.upload_dir)
    upload_bytes = sum(path.stat().st_size for path in upload_dir.rglob("*") if path.is_file()) if upload_dir.exists() else 0

    counts = {
        "customers": db.execute(text("SELECT COUNT(*) FROM customers")).scalar() or 0,
        "customer_intelligence": db.execute(text("SELECT COUNT(*) FROM customer_intelligence")).scalar() or 0,
        "raw_customer_data": db.query(func.count(RawCustomerData.id)).scalar() or 0,
        "upload_rollup": db.execute(text("SELECT COUNT(*) FROM upload_rollup")).scalar() or 0,
        "raw_upload": db.query(func.count(RawUpload.upload_id)).scalar() or 0,
        "export_job": db.query(func.count(ExportJob.export_id)).scalar() or 0,
        "audit_log": db.query(func.count(AuditLog.audit_id)).scalar() or 0,
    }

    db_size_mb = None
    if is_postgres():
        db_size_mb = round(
            float(db.execute(text("SELECT pg_database_size(current_database())")).scalar() or 0) / (1024 * 1024),
            2,
        )

    table_sizes = []
    if is_postgres():
        rows = db.execute(
            text(
                """
                SELECT relname, pg_total_relation_size(relid)
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(relid) DESC
                LIMIT 15
                """
            )
        ).fetchall()
        table_sizes = [
            {"table": name, "size_mb": round(float(size or 0) / (1024 * 1024), 2)}
            for name, size in rows
        ]

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "database_backend": "postgresql" if is_postgres() else "sqlite",
        "database_size_mb": db_size_mb,
        "upload_dir_bytes": upload_bytes,
        "upload_dir_mb": round(upload_bytes / (1024 * 1024), 2),
        "row_counts": counts,
        "top_tables_mb": table_sizes,
    }


def write_storage_audit_report(db: Session) -> Path:
    report = build_storage_audit(db)
    report_dir = Path(settings.ops_report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    filename = f"storage_audit_{datetime.utcnow().strftime('%Y%m%d')}.json"
    path = report_dir / filename
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info("storage_audit_written path=%s db_mb=%s upload_mb=%s", path, report.get("database_size_mb"), report.get("upload_dir_mb"))
    return path


def run_nightly_maintenance(db: Session) -> dict:
    result = {
        "materialized_views": refresh_materialized_views_job(),
        "vacuum_analyze": vacuum_analyze_job(),
        "exports_removed": 0,
        "export_files_removed": 0,
        "temp_files_removed": cleanup_temp_directories(),
        "upload_archives_removed": cleanup_old_upload_archives(),
        "audit_archived": 0,
    }
    exports_removed, export_files = cleanup_exports(db)
    result["exports_removed"] = exports_removed
    result["export_files_removed"] = export_files
    if datetime.utcnow().day <= 3:
        result["audit_archived"] = archive_audit_logs(db)
    return result


def run_weekly_maintenance(db: Session) -> dict:
    result = {
        "reindexed_tables": reindex_tables_job(),
        "storage_report": str(write_storage_audit_report(db)),
    }
    return result
