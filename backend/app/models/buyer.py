"""Buyer purchase facts linked to buyer uploads (no intelligence pipeline)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BuyerPurchase(Base):
    __tablename__ = "buyer_purchases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    upload_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("raw_upload.upload_id"), nullable=False, index=True)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    product_raw: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sku_token: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(8), nullable=True)
    source_channel: Mapped[str | None] = mapped_column(String(32), nullable=True)
    matched_customer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("customers.customer_id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    upload = relationship("RawUpload", back_populates="buyer_purchases")
    matched_customer = relationship("Customer")
