"""Volume 11 Section 9 — Intelligence version history."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IntelligenceVersion(Base):
    __tablename__ = "intelligence_version"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customers.customer_id"), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    intelligence_json: Mapped[str] = mapped_column(Text, nullable=False)
    source_upload_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
