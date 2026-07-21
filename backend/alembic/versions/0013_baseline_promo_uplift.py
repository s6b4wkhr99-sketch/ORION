"""Baseline conversion + promo uplift columns on customer_intelligence."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0013_baseline_promo_uplift"
down_revision = "0012_sfmc_audience_segment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    intel_cols = {c["name"] for c in inspector.get_columns("customer_intelligence")}
    for col in ("baseline_conversion", "promo_uplift", "baseline_revenue"):
        if col not in intel_cols:
            op.add_column("customer_intelligence", sa.Column(col, sa.Float(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    intel_cols = {c["name"] for c in inspector.get_columns("customer_intelligence")}
    for col in ("baseline_revenue", "promo_uplift", "baseline_conversion"):
        if col in intel_cols:
            op.drop_column("customer_intelligence", col)
