"""Layer 01 — Customer file upload: Raw → Mapping → Intelligence Pipeline."""

import json
import os
import uuid
from collections import Counter
from datetime import datetime

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.intelligence.datalogix_engine import preserve_datalogix_value
from app.intelligence.pipeline import run_intelligence_pipeline
from app.intelligence.trace_storage import BATCH_COMMIT_ROWS, BATCH_FLUSH_ROWS, persist_intelligence_result
from app.acquisition.rollup import build_upload_rollup
from app.cache.dashboard_cache import invalidate_dashboard_cache
from app.acquisition.upload_options import UploadOptions, resolve_upload_options
from app.models.customer import Customer, CustomerDatalogix
from app.models.raw import RawCustomerData, RawUpload
from app.models.zip import ZipIntelligence
from app.processing.duplicate import (
    batch_customers_by_email_keys,
    batch_existing_email_keys,
    classify_duplicate_in_file,
    find_in_file_duplicates,
    normalize_email_key,
)
from app.mapping.data_dictionary import (
    apply_internal_to_model_data,
    customer_internal_fields,
    db_column,
    datalogix_internal_fields,
    resolve_column,
)
from app.mapping.auto_engine import generate_mapping_report
from app.mapping.persistence import record_mapping_exceptions, record_mapping_history
from app.processing.mapper import build_column_map, extract_state_from_filename, validate_column_map
from app.processing.validator import is_valid_email
from app.utils.timezone import now_app_iso


class UploadValidationError(Exception):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}


def _safe_str(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def resolve_storage_path(relative_or_absolute: str) -> str:
    """Resolve upload/export paths relative to the backend root (stable across CWD)."""
    if os.path.isabs(relative_or_absolute):
        return relative_or_absolute
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(backend_root, relative_or_absolute)


def _load_dataframe(file_path: str, file_type: str) -> pd.DataFrame:
    resolved = resolve_storage_path(file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.isfile(resolved):
        raise UploadValidationError(
            f"Uploaded file not found on server: {resolved}",
            details={"file_path": resolved},
        )
    if file_type == "csv":
        return pd.read_csv(resolved, dtype=str, keep_default_na=False)
    return pd.read_excel(resolved, dtype=str, keep_default_na=False)


def _get_zip_ref(db: Session, zip_code: str | None, cache: dict[str, dict] | None = None) -> dict | None:
    if not zip_code:
        return None
    if cache is not None:
        return cache.get(zip_code)
    ref = db.query(ZipIntelligence).filter(ZipIntelligence.zip == zip_code).first()
    if not ref:
        return None
    return {
        "state": ref.state,
        "zip": ref.zip,
        "top_50_income_rank": ref.top50_rank,
        "city": ref.city,
        "county": ref.county,
        "median_income": ref.median_income,
        "population": ref.population,
    }


def _load_zip_cache(db: Session) -> dict[str, dict]:
    cache: dict[str, dict] = {}
    for ref in db.query(ZipIntelligence).yield_per(5000):
        cache[ref.zip] = {
            "state": ref.state,
            "zip": ref.zip,
            "top_50_income_rank": ref.top50_rank,
            "city": ref.city,
            "county": ref.county,
            "median_income": ref.median_income,
            "population": ref.population,
        }
    return cache


def _upsert_datalogix(db: Session, customer: Customer, data: dict) -> None:
    profile = db.query(CustomerDatalogix).filter(
        CustomerDatalogix.customer_id == customer.customer_id
    ).first()
    if profile:
        for k, v in data.items():
            setattr(profile, k, v)
    else:
        db.add(CustomerDatalogix(customer_id=customer.customer_id, **data))


def _maybe_flush_commit(
    db: Session,
    rows_since_flush: int,
    rows_since_commit: int,
    *,
    commit_every: int = BATCH_COMMIT_ROWS,
) -> tuple[int, int]:
    if rows_since_flush >= BATCH_FLUSH_ROWS:
        db.flush()
        rows_since_flush = 0
    if rows_since_commit >= commit_every:
        db.commit()
        rows_since_commit = 0
    return rows_since_flush, rows_since_commit


def _update_upload_progress(
    db: Session,
    upload: RawUpload,
    *,
    total_rows: int,
    rows_processed: int,
    duplicates_skipped: int,
    options: UploadOptions,
) -> None:
    scanned = rows_processed + duplicates_skipped
    if scanned == 0 or scanned % options.progress_update_rows != 0:
        return
    progress_pct = round(min(99.0, (scanned / total_rows) * 100), 2) if total_rows else 0
    upload.summary_json = json.dumps(
        {
            "total_rows": total_rows,
            "rows_processed": rows_processed,
            "duplicates_skipped": duplicates_skipped,
            "progress_pct": progress_pct,
        }
    )
    db.commit()


def _archive_upload_file(file_path: str | None) -> str | None:
    if not file_path or not os.path.isfile(file_path) or not settings.archive_uploads_gzip:
        return file_path
    import gzip
    import shutil

    gz_path = f"{file_path}.gz"
    with open(file_path, "rb") as src, gzip.open(gz_path, "wb") as dst:
        shutil.copyfileobj(src, dst)
    os.remove(file_path)
    return gz_path


def _datalogix_data_from_row(row, column_map: dict[str, str | None]) -> dict:
    datalogix_internal = {}
    for field in datalogix_internal_fields():
        source_col = resolve_column(column_map, field)
        raw = _safe_str(row.get(source_col)) if source_col else None
        datalogix_internal[field] = preserve_datalogix_value(db_column(field), raw)
    return apply_internal_to_model_data(datalogix_internal)


def _audience_segment_data_from_row(row, column_map: dict[str, str | None]) -> dict:
    from app.reference.sfmc_audience_segments import audience_segment_payload

    def _field(name: str) -> str | None:
        source_col = resolve_column(column_map, name)
        return _safe_str(row.get(source_col)) if source_col else None

    return audience_segment_payload(
        segment_id=_field("segment_id"),
        segment_code=_field("segment_code"),
        segment_name=_field("segment_name"),
    )


def _persist_row_error(
    db: Session,
    upload: RawUpload,
    *,
    row_number: int,
    headers: list[str],
    row,
    error: str,
) -> None:
    payload = {
        "error": error,
        "row": {str(k): _safe_str(row.get(k)) for k in headers},
    }
    db.add(
        RawCustomerData(
            upload_id=upload.upload_id,
            row_number=row_number,
            json_data=json.dumps(payload),
        )
    )


def process_upload(
    db: Session,
    file_path: str,
    file_name: str,
    uploaded_by: str = "system",
    *,
    upload: RawUpload | None = None,
    options: UploadOptions | None = None,
) -> RawUpload:
    import time

    started = time.perf_counter()
    file_type = "csv" if file_name.lower().endswith(".csv") else "xlsx"
    df = _load_dataframe(file_path, file_type)
    headers = [str(c).strip() for c in df.columns]
    auto_report = generate_mapping_report(db, headers)
    column_map = build_column_map(db, headers)
    validation = validate_column_map(db, column_map)
    if not validation["is_valid"]:
        raise UploadValidationError(
            "Required columns not found via Auto Mapping Engine. Email mapping is required.",
            validation,
        )

    resolved_options = options or resolve_upload_options(len(df))
    state_hint = extract_state_from_filename(file_name)
    seen_in_file: set[str] = set()

    email_col = column_map.get("email")
    if email_col and email_col in df.columns:
        file_emails = [_safe_str(v) for v in df[email_col].tolist()]
    else:
        file_emails = []
    file_email_keys = {key for email in file_emails if (key := normalize_email_key(email))}
    existing_emails = batch_existing_email_keys(db, file_email_keys)
    customers_by_email = (
        batch_customers_by_email_keys(db, file_email_keys)
        if resolved_options.refresh_datalogix_on_duplicate
        else {}
    )
    zip_cache = _load_zip_cache(db)

    if upload is None:
        upload = RawUpload(
            filename=file_name,
            file_path=file_path,
            file_type=file_type,
            uploaded_by=uploaded_by,
            provider="customer_list",
            dataset_type="prospect",
            status="processing",
        )
        db.add(upload)
        db.flush()
    else:
        upload.status = "processing"
        upload.file_path = file_path
        upload.file_type = file_type
        if not upload.filename:
            upload.filename = file_name

    upload.summary_json = json.dumps(
        {
            "total_rows": len(df),
            "rows_processed": 0,
            "progress_pct": 2.0,
            "phase": "processing_rows",
        }
    )
    db.commit()

    record_mapping_history(db, str(upload.upload_id), file_name, auto_report["mapping_report"])
    record_mapping_exceptions(db, str(upload.upload_id), auto_report["mapping_report"])

    valid_emails = 0
    invalid_emails = 0
    missing_zip = 0
    missing_state = 0
    duplicates_skipped = 0
    duplicates_updated = 0
    rows_processed = 0
    row_errors: list[dict] = []
    prizm_counter: Counter = Counter()
    ceragem_counter: Counter = Counter()
    permission_counter: Counter = Counter()
    rows_since_flush = 0
    rows_since_commit = 0

    in_file_dupes = find_in_file_duplicates(file_emails)

    for row_number, (_, row) in enumerate(df.iterrows(), start=1):
        try:
            row_dict = {str(k): row.get(k) for k in headers}

            customer_data_internal = {}
            for field in customer_internal_fields():
                source_col = resolve_column(column_map, field)
                customer_data_internal[field] = _safe_str(row.get(source_col)) if source_col else None

            customer_data = apply_internal_to_model_data(customer_data_internal)
            customer_data.update(_audience_segment_data_from_row(row, column_map))
            email = customer_data.get("email")
            email_key = normalize_email_key(email)

            if email_key:
                if classify_duplicate_in_file(email, seen_in_file):
                    duplicates_skipped += 1
                    continue
                if email_key in existing_emails:
                    if resolved_options.refresh_datalogix_on_duplicate:
                        existing_customer = customers_by_email.get(email_key)
                        if existing_customer:
                            datalogix_data = _datalogix_data_from_row(row, column_map)
                            if any(v for v in datalogix_data.values()):
                                _upsert_datalogix(db, existing_customer, datalogix_data)
                                duplicates_updated += 1
                            segment_data = _audience_segment_data_from_row(row, column_map)
                            if any(segment_data.values()):
                                for key, value in segment_data.items():
                                    setattr(existing_customer, key, value)
                    duplicates_skipped += 1
                    continue

            raw_row = None

            customer = Customer(
                upload_id=upload.upload_id,
                is_duplicate=False,
                **customer_data,
            )
            db.add(customer)
            if email_key:
                existing_emails.add(email_key)

            if customer.customer_id is None:
                db.flush()

            datalogix_data = _datalogix_data_from_row(row, column_map)

            zip_ref = _get_zip_ref(db, customer.zip, zip_cache)
            pipeline = run_intelligence_pipeline(
                customer={
                    "email": customer.email,
                    "state": customer.state,
                    "zip": customer.zip,
                    "city": customer.city,
                },
                datalogix_raw=datalogix_data,
                zip_lookup=lambda z: _get_zip_ref(db, z, zip_cache),
                zip_ref=zip_ref,
                row=row_dict,
                headers=headers,
                column_map=column_map,
                filename_state=state_hint,
            )

            customer.state = pipeline.customer.get("state") or customer.state
            customer.zip = pipeline.customer.get("zip") or customer.zip

            if customer.customer_id is None:
                db.flush()
            _upsert_datalogix(db, customer, datalogix_data)
            result = pipeline.to_intelligence_dict()
            persist_intelligence_result(
                db,
                customer,
                result,
                store_full_trace=resolved_options.store_full_trace,
                record_versions=resolved_options.record_intelligence_versions,
                sync_recommendation=resolved_options.sync_recommendation,
            )

            if is_valid_email(customer.email):
                valid_emails += 1
            else:
                invalid_emails += 1
            if not customer.zip:
                missing_zip += 1
            if not customer.state:
                missing_state += 1
            permission_counter[customer.permission or "Unknown"] += 1
            prizm_counter[result["prizm_proxy_segment"]] += 1
            ceragem_counter[result["ceragem_segment"]] += 1
            rows_processed += 1
            rows_since_flush += 1
            rows_since_commit += 1
            rows_since_flush, rows_since_commit = _maybe_flush_commit(
                db,
                rows_since_flush,
                rows_since_commit,
                commit_every=resolved_options.commit_every_rows,
            )
            _update_upload_progress(
                db,
                upload,
                total_rows=len(df),
                rows_processed=rows_processed,
                duplicates_skipped=duplicates_skipped,
                options=resolved_options,
            )

        except Exception as exc:
            row_errors.append({"row_number": row_number, "error": str(exc)})
            _persist_row_error(
                db,
                upload,
                row_number=row_number,
                headers=headers,
                row=row,
                error=str(exc),
            )

    db.flush()
    build_upload_rollup(db, upload.upload_id)

    customers_linked = (
        db.query(func.count(Customer.customer_id))
        .filter(Customer.upload_id == upload.upload_id)
        .scalar()
    ) or 0

    summary = {
        "total_rows": len(df),
        "rows_processed": int(customers_linked),
        "row_errors": row_errors,
        "valid_emails": valid_emails,
        "invalid_emails": invalid_emails,
        "missing_zip": missing_zip,
        "missing_state": missing_state,
        "duplicates_skipped": duplicates_skipped,
        "duplicates_updated": duplicates_updated,
        "duplicate_emails_in_file": in_file_dupes,
        "validation": validation,
        "contact_permission": dict(permission_counter),
        "prizm_distribution": dict(prizm_counter),
        "ceragem_distribution": dict(ceragem_counter),
        "column_map": validation["mapped_columns"],
        "mapping_report": auto_report["mapping_report"],
        "mapping_summary": auto_report["summary"],
        "storage_profile": "phase1_tiered_trace_bulk" if not resolved_options.store_full_trace else "phase1_tiered_trace",
        "bulk_mode": not resolved_options.store_full_trace,
        "store_raw_rows": False,
        "store_full_trace": resolved_options.store_full_trace,
        "sync_recommendation": resolved_options.sync_recommendation,
        "refresh_datalogix_on_duplicate": resolved_options.refresh_datalogix_on_duplicate,
        "commit_every_rows": resolved_options.commit_every_rows,
        "progress_pct": 100,
        "completed_at": now_app_iso(),
    }

    upload.status = "completed"
    upload.summary_json = json.dumps(summary)
    upload.file_path = _archive_upload_file(upload.file_path)
    processing_ms = round((time.perf_counter() - started) * 1000, 2)
    from app.schema.triggers import record_upload_history
    from app.schema.mv_reads import refresh_dashboard_materialized_views

    record_upload_history(
        db,
        upload_id=upload.upload_id,
        customer_count=int(customers_linked),
        duplicate_count=duplicates_skipped,
        warning_count=invalid_emails + missing_zip + len(row_errors),
        processing_time=processing_ms,
    )
    db.commit()
    db.refresh(upload)

    invalidate_dashboard_cache()
    try:
        refresh_dashboard_materialized_views()
    except Exception:
        pass

    from app.utils.audit_log import audit_intelligence, audit_mapping, audit_upload, audit_validation

    audit_upload(file_name, str(upload.upload_id), "completed", rows=rows_processed)
    audit_validation(str(upload.upload_id), validation["is_valid"], warnings=len(row_errors))
    audit_mapping(str(upload.upload_id), len(validation.get("mapped_columns", {})))
    audit_intelligence(str(upload.upload_id), rows_processed)

    return upload


def save_upload_file(content: bytes, filename: str) -> str:
    now = datetime.utcnow()
    upload_root = resolve_storage_path(settings.upload_dir)
    month_dir = os.path.join(upload_root, now.strftime("%Y"), now.strftime("%m"))
    os.makedirs(month_dir, exist_ok=True)
    ext = os.path.splitext(filename)[1]
    stored_name = f"{uuid.uuid4()}{ext}"
    path = os.path.abspath(os.path.join(month_dir, stored_name))
    with open(path, "wb") as f:
        f.write(content)
    return path
