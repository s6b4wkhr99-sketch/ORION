"""Phase 2 — Async customer upload queue (DB-backed, worker-polled)."""

from __future__ import annotations

import json
import os
import uuid

from sqlalchemy.orm import Session

from app.acquisition.upload import UploadValidationError, process_upload
from app.models.raw import RawUpload
from app.utils.timezone import now_app_iso


def enqueue_customer_upload(
    db: Session,
    *,
    file_path: str,
    file_name: str,
    uploaded_by: str,
) -> RawUpload:
    file_type = "csv" if file_name.lower().endswith(".csv") else "xlsx"
    upload = RawUpload(
        filename=file_name,
        file_path=file_path,
        file_type=file_type,
        uploaded_by=uploaded_by,
        provider="customer_list",
        dataset_type="prospect",
        status="pending",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def get_upload_status(db: Session, upload_id: str) -> dict | None:
    try:
        uid = uuid.UUID(upload_id)
    except ValueError:
        return None
    upload = db.query(RawUpload).filter(RawUpload.upload_id == uid).first()
    if not upload:
        return None
    return upload_status_payload(upload)


def upload_status_payload(upload: RawUpload) -> dict:
    summary: dict = {}
    if upload.summary_json:
        try:
            summary = json.loads(upload.summary_json)
        except json.JSONDecodeError:
            summary = {}

    total_rows = int(summary.get("total_rows") or 0)
    rows_processed = int(summary.get("rows_processed") or 0)
    duplicates_skipped = int(summary.get("duplicates_skipped") or 0)
    scanned = rows_processed + duplicates_skipped
    progress_pct = float(summary.get("progress_pct") or 0.0)
    if upload.status == "completed":
        progress_pct = 100.0
    elif upload.status == "pending":
        progress_pct = 0.0
    elif total_rows and scanned:
        progress_pct = round(min(99.0, (scanned / total_rows) * 100), 2)

    warnings = int(summary.get("invalid_emails", 0)) + int(summary.get("missing_zip", 0))
    return {
        "uploadId": str(upload.upload_id),
        "status": upload.status,
        "fileName": upload.filename,
        "customers": rows_processed,
        "totalRows": total_rows,
        "updated": int(summary.get("duplicates_skipped", summary.get("duplicates_updated", 0))),
        "warnings": warnings,
        "progressPct": progress_pct,
        "error": summary.get("error"),
        "storageProfile": summary.get("storage_profile"),
        "createdAt": upload.uploaded_date.isoformat() if upload.uploaded_date else None,
        "completedAt": summary.get("completed_at"),
    }


def _upload_file_ready(upload: RawUpload) -> bool:
    return bool(upload.file_path and os.path.isfile(upload.file_path))


def claim_resumable_processing_upload(db: Session) -> RawUpload | None:
    """Resume an upload interrupted by worker restart (same file, skip existing emails)."""
    upload = (
        db.query(RawUpload)
        .filter(RawUpload.status == "processing", RawUpload.provider == "customer_list")
        .order_by(RawUpload.uploaded_date.asc())
        .first()
    )
    if not upload or not _upload_file_ready(upload):
        return None
    return upload


def claim_next_pending_upload(db: Session) -> RawUpload | None:
    upload = (
        db.query(RawUpload)
        .filter(RawUpload.status == "pending", RawUpload.provider == "customer_list")
        .order_by(RawUpload.uploaded_date.asc())
        .first()
    )
    if not upload:
        return None
    upload.status = "processing"
    upload.summary_json = json.dumps(
        {
            "total_rows": 0,
            "rows_processed": 0,
            "progress_pct": 0,
            "started_at": now_app_iso(),
        }
    )
    db.commit()
    db.refresh(upload)
    return upload


def claim_next_upload(db: Session) -> RawUpload | None:
    """Prefer resuming interrupted processing jobs, then claim the oldest pending upload."""
    resumed = claim_resumable_processing_upload(db)
    if resumed:
        return resumed
    return claim_next_pending_upload(db)


def mark_upload_failed(db: Session, upload: RawUpload, message: str) -> None:
    upload_id = upload.upload_id
    db.rollback()
    upload = db.query(RawUpload).filter(RawUpload.upload_id == upload_id).first()
    if not upload:
        return
    summary: dict = {}
    if upload.summary_json:
        try:
            summary = json.loads(upload.summary_json)
        except json.JSONDecodeError:
            summary = {}
    summary["error"] = message
    summary["failed_at"] = now_app_iso()
    upload.status = "failed"
    upload.summary_json = json.dumps(summary)
    db.commit()


def run_worker_cycle(db: Session) -> bool:
    """Process one pending or resumable upload. Returns True if work was performed."""
    upload = claim_next_upload(db)
    if not upload:
        return False
    if not upload.file_path:
        mark_upload_failed(db, upload, "Upload file path missing")
        return True
    try:
        process_upload(
            db,
            upload.file_path,
            upload.filename,
            uploaded_by=upload.uploaded_by or "system",
            upload=upload,
        )
    except UploadValidationError as exc:
        mark_upload_failed(db, upload, str(exc))
    except Exception as exc:
        db.rollback()
        mark_upload_failed(db, upload, f"Upload processing failed: {exc}")
    return True
