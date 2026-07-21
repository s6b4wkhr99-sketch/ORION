"""Volume 16 — Supplemental physical schema tables."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UploadHistory(Base):
    __tablename__ = "upload_history"

    history_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    upload_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("raw_upload.upload_id"), nullable=False, index=True)
    customer_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class CampaignTarget(Base):
    __tablename__ = "campaign_target"

    target_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[str] = mapped_column(String(64), ForeignKey("campaign.campaign_id"), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customers.customer_id"), nullable=False, index=True)
    recommended_product: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expected_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    campaign_priority: Mapped[float | None] = mapped_column(Float, nullable=True)


class CampaignReport(Base):
    __tablename__ = "campaign_report"

    report_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[str] = mapped_column(String(64), ForeignKey("campaign.campaign_id"), nullable=False, index=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total_sent: Mapped[int] = mapped_column(Integer, default=0)
    delivered: Mapped[int] = mapped_column(Integer, default=0)
    opened: Mapped[int] = mapped_column(Integer, default=0)
    clicked: Mapped[int] = mapped_column(Integer, default=0)
    unique_click: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[float | None] = mapped_column(Float, nullable=True)
    ctor: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    conversion: Mapped[float | None] = mapped_column(Float, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendation"

    recommendation_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customers.customer_id"), nullable=False, index=True)
    recommended_product: Mapped[str | None] = mapped_column(String(64), nullable=True)
    recommended_message: Mapped[str | None] = mapped_column(String(256), nullable=True)
    recommended_campaign: Mapped[str | None] = mapped_column(String(256), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    learning_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    engine_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    generated_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ranking_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    scores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    audit_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProviderMaster(Base):
    __tablename__ = "provider"

    provider_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    provider_version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProviderFieldMapping(Base):
    __tablename__ = "provider_field_mapping"
    __table_args__ = (UniqueConstraint("provider_id", "internal_field", name="uk_provider_internal_field"),)

    mapping_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[int] = mapped_column(Integer, ForeignKey("provider.provider_id"), nullable=False, index=True)
    internal_field: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_field: Mapped[str] = mapped_column(String(128), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RoleDefinition(Base):
    __tablename__ = "role"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)


class PermissionDefinition(Base):
    __tablename__ = "permission"

    permission_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    permission_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
