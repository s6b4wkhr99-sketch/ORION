"""Phase A — Async export queue (DB-backed, worker-polled)."""

from __future__ import annotations

import json
import uuid

from sqlalchemy.orm import Session

from app.models.export import ExportJob
from app.providers.export_engine import run_provider_export
from app.providers.export_validation import ExportValidationError
from app.utils.timezone import now_app


def enqueue_export(
    db: Session,
    *,
    provider_name: str = "Generic CSV",
    campaign_name: str = "Ceragem Campaign",
    campaign_id: str = "CAMP-001",
    state_filter: str | None = None,
    zip_filter: str | None = None,
    segment_filter: str | None = None,
    product_filter: str | None = None,
    message_direction_filter: str | None = None,
    upload_id: str | None = None,
    user_id: str | None = None,
    role: str | None = None,
) -> ExportJob:
    job = ExportJob(
        provider=provider_name,
        campaign=campaign_name,
        segment_filter=segment_filter,
        state_filter=state_filter,
        status="pending",
        request_json=json.dumps({
            "provider_name": provider_name,
            "campaign_name": campaign_name,
            "campaign_id": campaign_id,
            "state_filter": state_filter,
            "zip_filter": zip_filter,
            "segment_filter": segment_filter,
            "product_filter": product_filter,
            "message_direction_filter": message_direction_filter,
            "upload_id": upload_id,
            "user_id": user_id,
            "role": role,
        }),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def export_status_payload(job: ExportJob) -> dict:
    return {
        "exportId": str(job.export_id),
        "status": job.status or "completed",
        "provider": job.provider,
        "campaign": job.campaign,
        "customerCount": job.customer_count,
        "error": job.error_message,
        "downloadUrl": f"/api/v1/export/download/{job.export_id}" if job.status == "completed" and job.download_url else None,
        "createdAt": job.created_at.isoformat() if job.created_at else None,
        "completedAt": job.completed_at.isoformat() if job.completed_at else None,
    }


def run_export_cycle(db: Session) -> bool:
    job = (
        db.query(ExportJob)
        .filter(ExportJob.status == "pending")
        .order_by(ExportJob.created_at.asc())
        .first()
    )
    if not job:
        return False

    job.status = "processing"
    db.commit()

    try:
        params = json.loads(job.request_json or "{}")
        file_path, completed = run_provider_export(
            db,
            provider_name=params.get("provider_name", job.provider),
            campaign_name=params.get("campaign_name", job.campaign or "Ceragem Campaign"),
            campaign_id=params.get("campaign_id", "CAMP-001"),
            state_filter=params.get("state_filter"),
            zip_filter=params.get("zip_filter"),
            segment_filter=params.get("segment_filter"),
            product_filter=params.get("product_filter"),
            message_direction_filter=params.get("message_direction_filter"),
            upload_id=params.get("upload_id"),
            user_id=params.get("user_id"),
            role=params.get("role"),
            existing_job=job,
        )
        job.status = "completed"
        job.download_url = file_path
        job.file_name = completed.file_name
        job.customer_count = completed.customer_count
        job.error_message = None
        job.completed_at = now_app()
        db.commit()
        return True
    except ExportValidationError as exc:
        job.status = "failed"
        job.error_message = "; ".join(exc.errors)
        job.completed_at = now_app()
        db.commit()
        return True
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = now_app()
        db.commit()
        return True
