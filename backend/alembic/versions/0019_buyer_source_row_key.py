"""Buyer purchase source_row_key for per-transaction dedup (allows repeat buyers)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0019_buyer_source_row_key"
down_revision = "0018_user_allowed_modules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "buyer_purchases" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("buyer_purchases")}
    if "source_row_key" not in columns:
        op.add_column("buyer_purchases", sa.Column("source_row_key", sa.String(length=64), nullable=True))
        op.create_index("idx_buyer_purchases_source_row_key", "buyer_purchases", ["source_row_key"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "buyer_purchases" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("buyer_purchases")}
    if "source_row_key" in columns:
        op.drop_index("idx_buyer_purchases_source_row_key", table_name="buyer_purchases")
        op.drop_column("buyer_purchases", "source_row_key")
