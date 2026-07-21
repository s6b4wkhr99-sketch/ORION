"""Audience export recommendation table for Opportunity Finder saves."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0014_audience_export"
down_revision = "0013_baseline_promo_uplift"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "audience_export_recommendation" in inspector.get_table_names():
        return
    op.create_table(
        "audience_export_recommendation",
        sa.Column("recommendation_id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("main_sku", sa.String(length=128), nullable=False),
        sa.Column("additional_skus_json", sa.Text(), nullable=True),
        sa.Column("states_json", sa.Text(), nullable=True),
        sa.Column("segment_filters_json", sa.Text(), nullable=True),
        sa.Column("upload_id", sa.Uuid(), nullable=True),
        sa.Column("forecast_customers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("forecast_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("predicted_conversion", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expected_orders", sa.Float(), nullable=False, server_default="0"),
        sa.Column("geo_scope", sa.String(length=512), nullable=False, server_default="National"),
        sa.Column("created_by", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "audience_export_recommendation" not in inspector.get_table_names():
        return
    op.drop_table("audience_export_recommendation")
