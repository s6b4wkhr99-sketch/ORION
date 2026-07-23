"""Commercial Simulator saved campaign forecasts."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0017_simulator_forecast"
down_revision = "0016_buyer_upload_gap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "commercial_simulator_forecast" in inspector.get_table_names():
        return
    op.create_table(
        "commercial_simulator_forecast",
        sa.Column("forecast_id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("main_sku", sa.String(length=128), nullable=False),
        sa.Column("additional_skus_json", sa.Text(), nullable=True),
        sa.Column("target_customers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expected_orders", sa.Float(), nullable=False, server_default="0"),
        sa.Column("revenue_forecast", sa.Float(), nullable=False, server_default="0"),
        sa.Column("net_profit", sa.Float(), nullable=False, server_default="0"),
        sa.Column("conversion_prediction", sa.Float(), nullable=False, server_default="0"),
        sa.Column("opportunity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("audience_file_name", sa.String(length=512), nullable=True),
        sa.Column("inputs_json", sa.Text(), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=False),
        sa.Column("audience_json", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "commercial_simulator_forecast" not in inspector.get_table_names():
        return
    op.drop_table("commercial_simulator_forecast")
