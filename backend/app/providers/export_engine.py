"""Volume 15 Section 5 — Export engine orchestration."""

import csv
import os
import time
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.mapping.data_dictionary import EXPORT_VALUE_RESOLVERS
from app.models.customer import Customer, CustomerIntelligence
from app.models.export import ExportJob
from app.providers.audit import log_provider_audit
from app.providers.base import ExportContext
from app.providers.export_builder import get_export_headers, resolve_export_value
from app.providers.export_validation import ExportValidationError, validate_export

EXPORT_BATCH_SIZE = 5000


def _apply_export_filters(q, *, upload_id, state_filter, zip_filter, segment_filter, product_filter, message_direction_filter):
    if upload_id:
        q = q.filter(Customer.upload_id == uuid.UUID(upload_id))
    if state_filter:
        q = q.filter(Customer.state == state_filter)
    if zip_filter:
        q = q.filter(Customer.zip == zip_filter)
    if segment_filter:
        q = q.filter(CustomerIntelligence.prizm_proxy_segment == segment_filter)
    if product_filter:
        q = q.filter(CustomerIntelligence.recommended_product == product_filter)
    if message_direction_filter:
        q = q.filter(CustomerIntelligence.message_direction == message_direction_filter)
    return q


def _iter_export_rows(db: Session, **filters):
    q = _apply_export_filters(
        db.query(Customer, CustomerIntelligence).join(
            CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id
        ),
        **filters,
    ).order_by(Customer.customer_id)
    offset = 0
    while True:
        batch = q.offset(offset).limit(EXPORT_BATCH_SIZE).all()
        if not batch:
            break
        yield from batch
        offset += EXPORT_BATCH_SIZE


def _write_export_csv(
    db: Session,
    *,
    provider_name: str,
    campaign_name: str,
    campaign_id: str,
    filters: dict,
) -> tuple[str, str, int, list[str], float]:
    started = time.perf_counter()
    headers = get_export_headers(db, provider_name)
    fieldnames = [label for _, label in headers]
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_name = f"export_{provider_name.replace(' ', '_').lower()}_{uuid.uuid4().hex[:8]}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    file_path = os.path.join(settings.upload_dir, file_name)
    customer_count = 0

    with open(file_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for customer, intel in _iter_export_rows(db, **filters):
            row_values: dict[str, str] = {}
            for field, label in headers:
                if field == "campaign_id":
                    row_values[label] = campaign_id
                elif field == "campaign_name":
                    row_values[label] = campaign_name
                elif field == "ceragem_segment":
                    row_values[label] = intel.ceragem_segment or intel.prizm_proxy_segment or ""
                elif field.startswith("intel_"):
                    intel_field = field.replace("intel_", "")
                    resolver = EXPORT_VALUE_RESOLVERS.get(intel_field)
                    row_values[label] = resolver(customer, intel) if resolver else ""
                else:
                    row_values[label] = resolve_export_value(field, customer, intel)
            writer.writerow(row_values)
            customer_count += 1

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    return file_path, file_name, customer_count, fieldnames, duration_ms


def run_provider_export(
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
    existing_job: ExportJob | None = None,
) -> tuple[str, ExportJob]:
    filters = {
        "upload_id": upload_id,
        "state_filter": state_filter,
        "zip_filter": zip_filter,
        "segment_filter": segment_filter,
        "product_filter": product_filter,
        "message_direction_filter": message_direction_filter,
    }
    file_path, file_name, customer_count, fieldnames, duration_ms = _write_export_csv(
        db,
        provider_name=provider_name,
        campaign_name=campaign_name,
        campaign_id=campaign_id,
        filters=filters,
    )

    ctx = ExportContext(
        provider_name=provider_name,
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        rows=[],
    )
    with open(file_path, encoding="utf-8") as handle:
        csv_content = handle.read()
    validation = validate_export(ctx, csv_content, fieldnames)
    if not validation.is_valid:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise ExportValidationError(validation.errors)

    if existing_job is not None:
        job = existing_job
        job.provider = provider_name
        job.campaign = campaign_name
        job.file_name = file_name
        job.download_url = file_path
        job.segment_filter = segment_filter
        job.state_filter = state_filter
        job.customer_count = customer_count
        job.status = "completed"
        job.error_message = None
    else:
        job = ExportJob(
            provider=provider_name,
            campaign=campaign_name,
            file_name=file_name,
            download_url=file_path,
            segment_filter=segment_filter,
            state_filter=state_filter,
            status="completed",
            customer_count=customer_count,
        )
        db.add(job)
    db.commit()
    db.refresh(job)

    log_provider_audit(
        db,
        action="provider_export",
        provider=provider_name,
        campaign_id=campaign_id,
        export_id=str(job.export_id),
        user_id=user_id,
        role=role,
        customer_count=customer_count,
        status="success",
        duration_ms=duration_ms,
        warnings=validation.warnings,
    )

    from app.utils.audit_log import audit_export

    audit_export(str(job.export_id), provider_name, campaign_name)
    return file_path, job
