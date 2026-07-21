"""Commercial Intelligence — persist commercial fields on customer_intelligence."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0010_commercial_intelligence"
down_revision = "0009_phase_c_ops"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if "commercial_catalog_version" not in tables:
        op.create_table(
            "commercial_catalog_version",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("version", sa.String(length=32), nullable=False),
            sa.Column("catalog_json", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("created_by", sa.String(length=320), nullable=True),
            sa.Column("approved_by", sa.String(length=320), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_commercial_catalog_version", "commercial_catalog_version", ["version"], unique=False)

    intel_cols = {c["name"] for c in inspector.get_columns("customer_intelligence")}
    if "price_resistance_score" not in intel_cols:
        op.add_column("customer_intelligence", sa.Column("price_resistance_score", sa.Float(), nullable=True))
    if "recommended_promotion" not in intel_cols:
        op.add_column("customer_intelligence", sa.Column("recommended_promotion", sa.Float(), nullable=True))
    if "promo_code" not in intel_cols:
        op.add_column("customer_intelligence", sa.Column("promo_code", sa.String(length=32), nullable=True))
    if "commercial_version" not in intel_cols:
        op.add_column("customer_intelligence", sa.Column("commercial_version", sa.String(length=32), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    intel_cols = {c["name"] for c in inspector.get_columns("customer_intelligence")}
    for col in ("commercial_version", "promo_code", "recommended_promotion", "price_resistance_score"):
        if col in intel_cols:
            op.drop_column("customer_intelligence", col)
    if "commercial_catalog_version" in inspector.get_table_names():
        op.drop_index("idx_commercial_catalog_version", table_name="commercial_catalog_version")
        op.drop_table("commercial_catalog_version")
