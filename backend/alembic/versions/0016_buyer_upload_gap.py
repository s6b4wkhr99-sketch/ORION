"""Buyer upload dataset_type + buyer_purchases table."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0016_buyer_upload_gap"
down_revision = "0015_perf_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("raw_upload")}
    if "dataset_type" not in columns:
        op.add_column(
            "raw_upload",
            sa.Column("dataset_type", sa.String(length=32), nullable=False, server_default="prospect"),
        )
        op.create_index("idx_raw_upload_dataset_type", "raw_upload", ["dataset_type", "status"])

    if "buyer_purchases" not in inspector.get_table_names():
        op.create_table(
            "buyer_purchases",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("upload_id", sa.Uuid(), sa.ForeignKey("raw_upload.upload_id"), nullable=False),
            sa.Column("row_number", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("product_raw", sa.String(length=512), nullable=True),
            sa.Column("sku_token", sa.String(length=16), nullable=True),
            sa.Column("state", sa.String(length=8), nullable=True),
            sa.Column("source_channel", sa.String(length=32), nullable=True),
            sa.Column("matched_customer_id", sa.Uuid(), sa.ForeignKey("customers.customer_id"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("idx_buyer_purchases_upload", "buyer_purchases", ["upload_id"])
        op.create_index("idx_buyer_purchases_email", "buyer_purchases", ["email"])
        op.create_index("idx_buyer_purchases_sku", "buyer_purchases", ["sku_token"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "buyer_purchases" in inspector.get_table_names():
        op.drop_table("buyer_purchases")
    columns = {c["name"] for c in inspector.get_columns("raw_upload")}
    if "dataset_type" in columns:
        op.drop_index("idx_raw_upload_dataset_type", table_name="raw_upload")
        op.drop_column("raw_upload", "dataset_type")
