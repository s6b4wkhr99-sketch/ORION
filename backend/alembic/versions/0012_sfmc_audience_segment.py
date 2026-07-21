"""Add SFMC audience segment columns to customers."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0012_sfmc_audience_segment"
down_revision = "0011_datalogix_dma"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("customers")}

    if "sfmc_segment_id" not in columns:
        op.add_column("customers", sa.Column("sfmc_segment_id", sa.String(length=32), nullable=True))
        op.create_index("ix_customers_sfmc_segment_id", "customers", ["sfmc_segment_id"], unique=False)
    if "sfmc_segment_code" not in columns:
        op.add_column("customers", sa.Column("sfmc_segment_code", sa.String(length=64), nullable=True))
        op.create_index("ix_customers_sfmc_segment_code", "customers", ["sfmc_segment_code"], unique=False)
    if "sfmc_segment_name" not in columns:
        op.add_column("customers", sa.Column("sfmc_segment_name", sa.String(length=128), nullable=True))
    if "audience_segment" not in columns:
        op.add_column("customers", sa.Column("audience_segment", sa.String(length=64), nullable=True))
        op.create_index("ix_customers_audience_segment", "customers", ["audience_segment"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("customers")}

    if "audience_segment" in columns:
        op.drop_index("ix_customers_audience_segment", table_name="customers")
        op.drop_column("customers", "audience_segment")
    if "sfmc_segment_name" in columns:
        op.drop_column("customers", "sfmc_segment_name")
    if "sfmc_segment_code" in columns:
        op.drop_index("ix_customers_sfmc_segment_code", table_name="customers")
        op.drop_column("customers", "sfmc_segment_code")
    if "sfmc_segment_id" in columns:
        op.drop_index("ix_customers_sfmc_segment_id", table_name="customers")
        op.drop_column("customers", "sfmc_segment_id")
