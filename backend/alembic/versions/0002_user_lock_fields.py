"""Volume 14 Section 13 — User account lock fields."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0002_user_lock_fields"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}
    with op.batch_alter_table("users") as batch_op:
        if "failed_login_attempts" not in columns:
            batch_op.add_column(sa.Column("failed_login_attempts", sa.Integer(), server_default="0", nullable=False))
        if "locked_at" not in columns:
            batch_op.add_column(sa.Column("locked_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}
    with op.batch_alter_table("users") as batch_op:
        if "locked_at" in columns:
            batch_op.drop_column("locked_at")
        if "failed_login_attempts" in columns:
            batch_op.drop_column("failed_login_attempts")
