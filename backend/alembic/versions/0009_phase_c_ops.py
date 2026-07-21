"""Phase C — audit_log_archive table for monthly retention."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0009_phase_c_ops"
down_revision = "0008_phase_a_export_async"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "audit_log_archive" in inspector.get_table_names():
        return
    op.create_table(
        "audit_log_archive",
        sa.Column("audit_id", sa.Uuid(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.String(length=320), nullable=True),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", sa.String(length=128), nullable=True),
        sa.Column("before_value", sa.Text(), nullable=True),
        sa.Column("after_value", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("browser", sa.String(length=256), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("archived_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("audit_id"),
    )
    op.create_index("idx_audit_archive_timestamp", "audit_log_archive", ["timestamp"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "audit_log_archive" not in inspector.get_table_names():
        return
    op.drop_index("idx_audit_archive_timestamp", table_name="audit_log_archive")
    op.drop_table("audit_log_archive")
