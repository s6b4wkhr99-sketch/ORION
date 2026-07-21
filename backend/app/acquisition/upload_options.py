"""Phase 2 — Upload processing options (bulk mode for 2.5M scale)."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class UploadOptions:
    store_raw_rows: bool = False
    store_full_trace: bool = True
    record_intelligence_versions: bool = True
    sync_recommendation: bool = True
    refresh_datalogix_on_duplicate: bool = False
    progress_update_rows: int = 5000
    commit_every_rows: int = 1000


def resolve_upload_options(total_rows: int) -> UploadOptions:
    """Apply bulk-mode defaults for large initial loads."""
    bulk = (
        settings.customer_analysis_only
        or settings.bulk_upload_mode
        or total_rows >= settings.bulk_upload_row_threshold
    )
    if not bulk:
        return UploadOptions()
    skip_raw = settings.bulk_upload_skip_raw_rows or settings.customer_analysis_only
    skip_trace = settings.bulk_upload_skip_full_trace or settings.customer_analysis_only
    skip_versions = settings.bulk_upload_skip_version_history or settings.customer_analysis_only
    return UploadOptions(
        store_raw_rows=False,
        store_full_trace=not skip_trace,
        record_intelligence_versions=not skip_versions,
        sync_recommendation=False,
        refresh_datalogix_on_duplicate=settings.upload_refresh_datalogix_on_duplicate,
        progress_update_rows=1000,
        commit_every_rows=settings.upload_commit_rows_bulk,
    )
