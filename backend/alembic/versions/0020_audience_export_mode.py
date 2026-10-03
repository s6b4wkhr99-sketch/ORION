"""Audience export recommended vs promo-reach extract mode."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0020_audience_export_mode"
down_revision = "0019_buyer_source_row_key"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "audience_export_recommendation" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("audience_export_recommendation")}
    if "audience_mode" not in columns:
        op.add_column(
            "audience_export_recommendation",
            sa.Column("audience_mode", sa.String(length=32), nullable=False, server_default="recommended"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "audience_export_recommendation" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("audience_export_recommendation")}
    if "audience_mode" in columns:
        op.drop_column("audience_export_recommendation", "audience_mode")
