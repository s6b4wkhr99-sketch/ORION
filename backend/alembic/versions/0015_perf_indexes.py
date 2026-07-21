"""Performance indexes for rollup and opportunity queries."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0015_perf_indexes"
down_revision = "0014_audience_export"
branch_labels = None
depends_on = None

INDEX_DDL = [
    "CREATE INDEX IF NOT EXISTS idx_customer_upload_state ON customers (upload_id, state)",
    "CREATE INDEX IF NOT EXISTS idx_upload_rollup_upload_dim ON upload_rollup (upload_id, dimension)",
    "CREATE INDEX IF NOT EXISTS idx_upload_rollup_dim_scope ON upload_rollup (dimension, scope)",
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    for ddl in INDEX_DDL:
        table = ddl.split(" ON ")[1].split(" ")[0]
        if table not in tables:
            continue
        op.execute(sa.text(ddl))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "customers" in inspector.get_table_names():
        op.execute(sa.text("DROP INDEX IF EXISTS idx_customer_upload_state"))
    if "upload_rollup" in inspector.get_table_names():
        op.execute(sa.text("DROP INDEX IF EXISTS idx_upload_rollup_upload_dim"))
        op.execute(sa.text("DROP INDEX IF EXISTS idx_upload_rollup_dim_scope"))
