"""Upload processing profile — exposed to Upload Center for large-scale loads."""

from __future__ import annotations

from app.acquisition.upload_options import resolve_upload_options
from app.config import settings


def get_upload_processing_profile(estimated_rows: int | None = None) -> dict:
    rows = estimated_rows or settings.bulk_upload_row_threshold
    options = resolve_upload_options(rows)
    bulk_active = settings.bulk_upload_mode or rows >= settings.bulk_upload_row_threshold

    return {
        "upload_async": settings.upload_async,
        "bulk_upload_mode": settings.bulk_upload_mode,
        "bulk_upload_row_threshold": settings.bulk_upload_row_threshold,
        "customer_analysis_only": settings.customer_analysis_only,
        "bulk_active_for_estimate": bulk_active,
        "store_raw_rows": options.store_raw_rows,
        "store_full_trace": options.store_full_trace,
        "record_intelligence_versions": options.record_intelligence_versions,
        "sync_recommendation": options.sync_recommendation,
        "refresh_datalogix_on_duplicate": options.refresh_datalogix_on_duplicate,
        "commit_every_rows": options.commit_every_rows,
        "progress_update_rows": options.progress_update_rows,
        "recommended_for_2_5m": {
            "database_url": "postgresql+psycopg2://cios:cios_dev_password@127.0.0.1:5432/cios",
            "upload_async": True,
            "bulk_upload_mode": True,
            "bulk_upload_skip_raw_rows": True,
            "bulk_upload_skip_full_trace": True,
            "bulk_upload_skip_version_history": True,
            "customer_analysis_only": True,
            "worker": "python -m app.worker.main",
        },
    }
