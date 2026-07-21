"""Layer 4 — Campaign Database."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Campaign(Base):
    __tablename__ = "campaign"

    campaign_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    campaign_name: Mapped[str] = mapped_column(String(256), nullable=False)
    campaign_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True, default="completed")
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(128), nullable=True, default="CIOS Admin")
    forecast_version: Mapped[str | None] = mapped_column(String(64), nullable=True, default="Volume 06 v1.0")
    forecast_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    forecast_orders: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_orders: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    states = relationship("CampaignState", back_populates="campaign")
    products = relationship("CampaignProduct", back_populates="campaign")
    segments = relationship("CampaignSegment", back_populates="campaign")


class CampaignState(Base):
    __tablename__ = "campaign_state"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[str] = mapped_column(String(64), ForeignKey("campaign.campaign_id"), nullable=False)
    state: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    sent: Mapped[int] = mapped_column(Integer, default=0)
    open: Mapped[int] = mapped_column(Integer, default=0)
    click: Mapped[int] = mapped_column(Integer, default=0)
    unique_click: Mapped[int] = mapped_column(Integer, default=0)
    conversion: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    open_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    ctr: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    roi: Mapped[float | None] = mapped_column(Float, nullable=True)

    campaign = relationship("Campaign", back_populates="states")


class CampaignProduct(Base):
    __tablename__ = "campaign_product"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[str] = mapped_column(String(64), ForeignKey("campaign.campaign_id"), nullable=False)
    product: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    click: Mapped[int] = mapped_column(Integer, default=0)
    conversion: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    click_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    campaign = relationship("Campaign", back_populates="products")


class CampaignSegment(Base):
    __tablename__ = "campaign_segment"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[str] = mapped_column(String(64), ForeignKey("campaign.campaign_id"), nullable=False)
    segment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customers: Mapped[int] = mapped_column(Integer, default=0)
    conversion: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue: Mapped[float | None] = mapped_column(Float, nullable=True)

    campaign = relationship("Campaign", back_populates="segments")


class CampaignReportUpload(Base):
    __tablename__ = "campaign_report_upload"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    campaign_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
