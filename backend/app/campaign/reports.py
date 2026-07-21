"""Campaign report import — Volume 15 Provider Integration Layer."""

from sqlalchemy.orm import Session

from app.models.campaign import CampaignReportUpload
from app.providers.import_engine import run_provider_import


def process_campaign_report(
    db: Session,
    file_path: str,
    file_name: str,
    *,
    provider_name: str | None = None,
    user_id: str | None = None,
    role: str | None = None,
) -> CampaignReportUpload:
    return run_provider_import(
        db,
        file_path,
        file_name,
        provider_name=provider_name,
        user_id=user_id,
        role=role,
    )
