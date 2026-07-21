"""Layer 2 — Mapping configuration (no hard-coded column names)."""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FieldMapping(Base):
    __tablename__ = "field_mapping"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_field: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    target_field: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    data_type: Mapped[str] = mapped_column(String(32), default="string")
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    mapping_rule: Mapped[str | None] = mapped_column(String(256), nullable=True)
    version: Mapped[str] = mapped_column(String(16), default="1.0")
