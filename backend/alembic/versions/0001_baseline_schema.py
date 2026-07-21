"""CIOS baseline schema — Volume 13 Section 17."""

from alembic import op

from app.database import Base
import app.models  # noqa: F401 — register ORM tables for create_all

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
