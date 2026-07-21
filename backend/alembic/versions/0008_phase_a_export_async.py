"""Phase A — export_job async columns."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0008_phase_a_export_async"
down_revision = "0007_phase1_trace_backfill"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "export_job" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("export_job")}
    if "status" not in columns:
        op.add_column("export_job", sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"))
    if "error_message" not in columns:
        op.add_column("export_job", sa.Column("error_message", sa.Text(), nullable=True))
    if "request_json" not in columns:
        op.add_column("export_job", sa.Column("request_json", sa.Text(), nullable=True))
    if "customer_count" not in columns:
        op.add_column("export_job", sa.Column("customer_count", sa.Integer(), nullable=True))
    if "completed_at" not in columns:
        op.add_column("export_job", sa.Column("completed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "export_job" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("export_job")}
    for name in ("completed_at", "customer_count", "request_json", "error_message", "status"):
        if name in columns:
            op.drop_column("export_job", name)
