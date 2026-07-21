"""Layer 4 — Export Database."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExportJob(Base):
    __tablename__ = "export_job"

    export_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    campaign: Mapped[str | None] = mapped_column(String(256), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    download_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    segment_filter: Mapped[str | None] = mapped_column(String(256), nullable=True)
    state_filter: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ExportTemplate(Base):
    __tablename__ = "export_template"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    field: Mapped[str] = mapped_column(String(64), nullable=False)
    target_name: Mapped[str] = mapped_column(String(128), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    required: Mapped[bool] = mapped_column(Boolean, default=False)


class AudienceExportRecommendation(Base):
    __tablename__ = "audience_export_recommendation"

    recommendation_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    main_sku: Mapped[str] = mapped_column(String(128), nullable=False)
    additional_skus_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    states_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    segment_filters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    upload_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    forecast_customers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forecast_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    predicted_conversion: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    expected_orders: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    geo_scope: Mapped[str] = mapped_column(String(512), nullable=False, default="National")
    created_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
