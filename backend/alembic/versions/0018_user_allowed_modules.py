"""User custom menu module overrides."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0018_user_allowed_modules"
down_revision = "0017_simulator_forecast"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "allowed_modules" not in columns:
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(sa.Column("allowed_modules", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "allowed_modules" in columns:
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_column("allowed_modules")
