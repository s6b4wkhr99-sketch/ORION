"""Volume 22 — Reference Data Library tables."""

from alembic import op

from app.database import Base
import app.models  # noqa: F401

revision = "0005_v22_reference_data"
down_revision = "0004_rfc001_auto_mapping"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = [
        "reference_data_version",
        "state_master",
        "county_master",
        "zip_master",
        "time_zone_master",
        "country_master",
        "gender_master",
        "generation_master",
        "household_master",
        "dwelling_master",
        "income_range_master",
        "product_master",
        "campaign_type_master",
        "campaign_status_master",
        "message_type_master",
        "holiday_master",
        "purchase_power_master",
        "pain_index_master",
        "lifestyle_master",
        "ceragem_segment_master",
        "priority_master",
        "prizm_segment_master",
        "provider_version_master",
        "provider_status_master",
        "dashboard_master",
        "metric_master",
        "chart_type_master",
        "language_master",
        "currency_master",
        "status_master",
    ]
    for name in tables:
        if name in Base.metadata.tables:
            Base.metadata.tables[name].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in reversed(
        [
            "status_master",
            "currency_master",
            "language_master",
            "chart_type_master",
            "metric_master",
            "dashboard_master",
            "provider_status_master",
            "provider_version_master",
            "prizm_segment_master",
            "priority_master",
            "ceragem_segment_master",
            "lifestyle_master",
            "pain_index_master",
            "purchase_power_master",
            "holiday_master",
            "message_type_master",
            "campaign_status_master",
            "campaign_type_master",
            "product_master",
            "income_range_master",
            "dwelling_master",
            "household_master",
            "generation_master",
            "gender_master",
            "country_master",
            "time_zone_master",
            "zip_master",
            "county_master",
            "state_master",
            "reference_data_version",
        ]
    ):
        if name in Base.metadata.tables:
            Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
