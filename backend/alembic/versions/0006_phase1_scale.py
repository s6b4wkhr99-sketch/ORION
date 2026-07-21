"""Phase 1 — Tiered trace storage and upload rollup tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0006_phase1_scale"
down_revision = "0005_v22_reference_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    ci_columns = {col["name"] for col in inspector.get_columns("customer_intelligence")}
    if "trace_summary_json" not in ci_columns:
        op.add_column("customer_intelligence", sa.Column("trace_summary_json", sa.Text(), nullable=True))
    if "framework_summary_json" not in ci_columns:
        op.add_column("customer_intelligence", sa.Column("framework_summary_json", sa.Text(), nullable=True))

    if "intelligence_trace" not in inspector.get_table_names():
        op.create_table(
            "intelligence_trace",
            sa.Column("customer_id", sa.Uuid(), nullable=False),
            sa.Column("trace_json", sa.Text(), nullable=False),
            sa.Column("framework_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.customer_id"]),
            sa.PrimaryKeyConstraint("customer_id"),
        )

    if "upload_rollup" not in inspector.get_table_names():
        op.create_table(
            "upload_rollup",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("upload_id", sa.Uuid(), nullable=False),
            sa.Column("dimension", sa.String(length=32), nullable=False),
            sa.Column("scope", sa.String(length=16), nullable=False),
            sa.Column("key", sa.String(length=128), nullable=False),
            sa.Column("customer_count", sa.Integer(), nullable=False),
            sa.Column("expected_orders", sa.Float(), nullable=False),
            sa.Column("expected_revenue", sa.Float(), nullable=False),
            sa.Column("payload_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["upload_id"], ["raw_upload.upload_id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_upload_rollup_upload_id", "upload_rollup", ["upload_id"])
        op.create_index("ix_upload_rollup_dimension", "upload_rollup", ["dimension"])
        op.create_index("ix_upload_rollup_scope", "upload_rollup", ["scope"])
        op.create_index("ix_upload_rollup_key", "upload_rollup", ["key"])


def downgrade() -> None:
    op.drop_index("ix_upload_rollup_key", table_name="upload_rollup")
    op.drop_index("ix_upload_rollup_scope", table_name="upload_rollup")
    op.drop_index("ix_upload_rollup_dimension", table_name="upload_rollup")
    op.drop_index("ix_upload_rollup_upload_id", table_name="upload_rollup")
    op.drop_table("upload_rollup")
    op.drop_table("intelligence_trace")
    op.drop_column("customer_intelligence", "framework_summary_json")
    op.drop_column("customer_intelligence", "trace_summary_json")
