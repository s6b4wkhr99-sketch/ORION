"""Add Datalogix DMA and county code columns."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0011_datalogix_dma"
down_revision = "0010_commercial_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("customer_datalogix")}

    if "dma_code" not in columns:
        op.add_column("customer_datalogix", sa.Column("dma_code", sa.String(length=8), nullable=True))
    if "county_code" not in columns:
        op.add_column("customer_datalogix", sa.Column("county_code", sa.String(length=8), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("customer_datalogix")}

    if "county_code" in columns:
        op.drop_column("customer_datalogix", "county_code")
    if "dma_code" in columns:
        op.drop_column("customer_datalogix", "dma_code")
