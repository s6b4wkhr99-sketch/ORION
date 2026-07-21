"""RFC-001 — supplemental auto mapping tables."""

from alembic import op

from app.database import Base
import app.models  # noqa: F401

revision = "0004_rfc001_auto_mapping"
down_revision = "0003_v16_physical"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = [
        "field_master",
        "field_alias",
        "provider_template",
        "mapping_history",
        "mapping_exception",
    ]
    for name in tables:
        if name in Base.metadata.tables:
            Base.metadata.tables[name].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in reversed(
        [
            "mapping_exception",
            "mapping_history",
            "provider_template",
            "field_alias",
            "field_master",
        ]
    ):
        if name in Base.metadata.tables:
            Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
