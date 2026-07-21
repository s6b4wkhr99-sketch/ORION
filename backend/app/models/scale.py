"""Phase 1 — Scale optimizations: tiered trace storage and upload rollups."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IntelligenceTrace(Base):
    """Full explainability payload — loaded on customer detail / framework APIs only."""

    __tablename__ = "intelligence_trace"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("customers.customer_id"), primary_key=True
    )
    trace_json: Mapped[str] = mapped_column(Text, nullable=False)
    framework_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UploadRollup(Base):
    """Pre-aggregated upload metrics for fast dashboards (no full-table scans)."""

    __tablename__ = "upload_rollup"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    upload_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("raw_upload.upload_id"), index=True)
    dimension: Mapped[str] = mapped_column(String(32), index=True)
    scope: Mapped[str] = mapped_column(String(16), default="*", index=True)
    key: Mapped[str] = mapped_column(String(128), index=True)
    customer_count: Mapped[int] = mapped_column(Integer, default=0)
    expected_orders: Mapped[float] = mapped_column(Float, default=0.0)
    expected_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
