"""Commercial Intelligence — versioned price guide storage."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CommercialCatalogVersion(Base):
    """Version-controlled commercial price guide (never overwrites — append-only with publish/rollback)."""

    __tablename__ = "commercial_catalog_version"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    version: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    catalog_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_by: Mapped[str | None] = mapped_column(String(320), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CommercialSimulatorForecast(Base):
    """Saved Commercial Simulator campaign forecast for later actual-vs-plan comparison."""

    __tablename__ = "commercial_simulator_forecast"

    forecast_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    main_sku: Mapped[str] = mapped_column(String(128), nullable=False)
    additional_skus_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_customers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expected_orders: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    revenue_forecast: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    net_profit: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    conversion_prediction: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    audience_file_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    inputs_json: Mapped[str] = mapped_column(Text, nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
    audience_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
