"""Volume 15 Section 17 — Provider mapping version registry."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProviderMappingVersion(Base):
    __tablename__ = "provider_mapping_version"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(128), default="CIOS Integration Team")
    compatibility_version: Mapped[str] = mapped_column(String(32), default="CIOS 1.0")
    status: Mapped[str] = mapped_column(String(32), default="active")
