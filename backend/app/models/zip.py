"""Layer 3 — ZIP Intelligence reference data."""

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ZipIntelligence(Base):
    __tablename__ = "zip_intelligence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zip: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    median_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    top50_rank: Mapped[bool] = mapped_column(default=False)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    county: Mapped[str | None] = mapped_column(String(128), nullable=True)
