"""CSV export entry point — Volume 15 Provider Integration Layer."""

from sqlalchemy.orm import Session

from app.models.export import ExportJob
from app.providers.constants import EXPORT_PROVIDERS, SUPPORTED_PROVIDERS
from app.providers.export_engine import run_provider_export
from app.providers.export_queue import enqueue_export

__all__ = ["SUPPORTED_PROVIDERS", "EXPORT_PROVIDERS", "generate_export", "enqueue_export_job"]


def enqueue_export_job(
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
    return enqueue_export(
        db,
        provider_name=provider_name,
        campaign_name=campaign_name,
        campaign_id=campaign_id,
        state_filter=state_filter,
        zip_filter=zip_filter,
        segment_filter=segment_filter,
        product_filter=product_filter,
        message_direction_filter=message_direction_filter,
        upload_id=upload_id,
        user_id=user_id,
        role=role,
    )


def generate_export(
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
) -> tuple[str, ExportJob]:
    return run_provider_export(
        db,
        provider_name=provider_name,
        campaign_name=campaign_name,
        campaign_id=campaign_id,
        state_filter=state_filter,
        zip_filter=zip_filter,
        segment_filter=segment_filter,
        product_filter=product_filter,
        message_direction_filter=message_direction_filter,
        upload_id=upload_id,
        user_id=user_id,
        role=role,
    )
