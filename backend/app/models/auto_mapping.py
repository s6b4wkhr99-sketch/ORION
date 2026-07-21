"""RFC-001 — Auto mapping database models."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FieldMaster(Base):
    __tablename__ = "field_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    internal_field: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(32), default="customer")
    data_type: Mapped[str] = mapped_column(String(32), default="string")
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    version: Mapped[str] = mapped_column(String(16), default="1.0")


class FieldAlias(Base):
    __tablename__ = "field_alias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alias_header: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    internal_field: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    match_type: Mapped[str] = mapped_column(String(32), default="alias")
    confidence: Mapped[float] = mapped_column(Float, default=98.0)
    approved: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[str] = mapped_column(String(16), default="1.0")


class ProviderUploadTemplate(Base):
    __tablename__ = "provider_template"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_header: Mapped[str] = mapped_column(String(128), nullable=False)
    internal_field: Mapped[str] = mapped_column(String(64), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=10)
    version: Mapped[str] = mapped_column(String(16), default="1.0")


class MappingHistory(Base):
    __tablename__ = "mapping_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    uploaded_header: Mapped[str] = mapped_column(String(128), nullable=False)
    internal_field: Mapped[str | None] = mapped_column(String(64), nullable=True)
    match_type: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(32), default="mapped")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MappingException(Base):
    __tablename__ = "mapping_exception"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    uploaded_header: Mapped[str] = mapped_column(String(128), nullable=False)
    suggestion: Mapped[str | None] = mapped_column(String(64), nullable=True)
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolution: Mapped[str] = mapped_column(String(32), default="ignored")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
