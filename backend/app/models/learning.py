"""Layer 5 — Learning Database."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LearningCampaign(Base):
    __tablename__ = "learning_campaign"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(256), nullable=True)
    cta: Mapped[str | None] = mapped_column(String(128), nullable=True)
    coupon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    product: Mapped[str | None] = mapped_column(String(64), nullable=True)
    segment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str | None] = mapped_column(String(8), nullable=True)
    zip: Mapped[str | None] = mapped_column(String(16), nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    insight_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent: Mapped[int] = mapped_column(Integer, default=0)
    open: Mapped[int] = mapped_column(Integer, default=0)
    click: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    roi: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_report_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CampaignLearning(Base):
    """Volume 06 Section 23 — Immutable campaign learning records."""

    __tablename__ = "campaign_learning"

    learning_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    campaign_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    campaign_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    audience_count: Mapped[int] = mapped_column(Integer, default=0)
    ceragem_segment_distribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    prizm_distribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_distribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_direction: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    roi: Mapped[float | None] = mapped_column(Float, nullable=True)
    ctr: Mapped[float | None] = mapped_column(Float, nullable=True)
    ctor: Mapped[float | None] = mapped_column(Float, nullable=True)
    orders: Mapped[float | None] = mapped_column(Float, nullable=True)
    conversion: Mapped[float | None] = mapped_column(Float, nullable=True)
    forecast_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    learning_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_report_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
