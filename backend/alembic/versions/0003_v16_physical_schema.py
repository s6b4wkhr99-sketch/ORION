"""Volume 16 — supplemental physical tables."""

from alembic import op

from app.database import Base
import app.models  # noqa: F401

revision = "0003_v16_physical"
down_revision = "0002_user_lock_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # New Volume 16 tables only — create_all on startup handles dev; migration for prod
    tables = [
        "upload_history",
        "campaign_target",
        "campaign_report",
        "recommendation",
        "provider",
        "provider_field_mapping",
        "role",
        "permission",
    ]
    for name in tables:
        if name in Base.metadata.tables:
            Base.metadata.tables[name].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in reversed(
        [
            "provider_field_mapping",
            "permission",
            "role",
            "provider",
            "recommendation",
            "campaign_report",
            "campaign_target",
            "upload_history",
        ]
    ):
        if name in Base.metadata.tables:
            Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
