"""Layer 1 — Raw Data (immutable source of truth)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RawUpload(Base):
    __tablename__ = "raw_upload"

    upload_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    uploaded_by: Mapped[str | None] = mapped_column(String(128), nullable=True, default="system")
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_version: Mapped[str | None] = mapped_column(String(32), nullable=True, default="1.0")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    raw_rows = relationship("RawCustomerData", back_populates="upload")
    customers = relationship("Customer", back_populates="upload")


class RawCustomerData(Base):
    __tablename__ = "raw_customer_data"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    upload_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("raw_upload.upload_id"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    json_data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    upload = relationship("RawUpload", back_populates="raw_rows")
