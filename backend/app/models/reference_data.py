"""Volume 22 — Reference Data Library physical models."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

RDL_TABLE_VERSION = "1.0"


class ReferenceDataVersion(Base):
    __tablename__ = "reference_data_version"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    library_version: Mapped[str] = mapped_column(String(32), nullable=False)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class StateMaster(Base):
    __tablename__ = "state_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False, index=True)
    state_name: Mapped[str] = mapped_column(String(64), nullable=False)
    region: Mapped[str | None] = mapped_column(String(32), nullable=True)
    time_zone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class CountyMaster(Base):
    __tablename__ = "county_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    county_name: Mapped[str] = mapped_column(String(64), nullable=False)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    fips_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class ZipMaster(Base):
    __tablename__ = "zip_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zip_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    state_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    county: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    median_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top_income_indicator: Mapped[bool] = mapped_column(Boolean, default=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class TimeZoneMaster(Base):
    __tablename__ = "time_zone_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    iana_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class CountryMaster(Base):
    __tablename__ = "country_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    country_name: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class GenderMaster(Base):
    __tablename__ = "gender_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(128), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class GenerationMaster(Base):
    __tablename__ = "generation_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(128), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class HouseholdMaster(Base):
    __tablename__ = "household_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(128), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class DwellingMaster(Base):
    __tablename__ = "dwelling_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(128), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class IncomeRangeMaster(Base):
    __tablename__ = "income_range_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(128), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class ProductMaster(Base):
    __tablename__ = "product_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(64), nullable=False)
    product_family: Mapped[str | None] = mapped_column(String(32), nullable=True)
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    launch_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    msrp: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_segment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class CampaignTypeMaster(Base):
    __tablename__ = "campaign_type_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class CampaignStatusMaster(Base):
    __tablename__ = "campaign_status_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class MessageTypeMaster(Base):
    __tablename__ = "message_type_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class HolidayMaster(Base):
    __tablename__ = "holiday_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class PurchasePowerMaster(Base):
    __tablename__ = "purchase_power_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    index_score: Mapped[float] = mapped_column(Float, default=0.0)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class PainIndexMaster(Base):
    __tablename__ = "pain_index_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    index_score: Mapped[float] = mapped_column(Float, default=0.0)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class LifestyleMaster(Base):
    __tablename__ = "lifestyle_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    index_score: Mapped[float] = mapped_column(Float, default=0.0)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class CeragemSegmentMaster(Base):
    __tablename__ = "ceragem_segment_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    segment_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    legacy_v04_segment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class PriorityMaster(Base):
    __tablename__ = "priority_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class PrizmSegmentMaster(Base):
    __tablename__ = "prizm_segment_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    segment_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class ProviderVersionMaster(Base):
    __tablename__ = "provider_version_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(16), nullable=False)
    compatibility_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class ProviderStatusMaster(Base):
    __tablename__ = "provider_status_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(128), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class DashboardMaster(Base):
    __tablename__ = "dashboard_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class MetricMaster(Base):
    __tablename__ = "metric_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class ChartTypeMaster(Base):
    __tablename__ = "chart_type_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class LanguageMaster(Base):
    __tablename__ = "language_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class CurrencyMaster(Base):
    __tablename__ = "currency_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(8), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")


class StatusMaster(Base):
    __tablename__ = "status_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(128), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    reference_version: Mapped[str] = mapped_column(String(16), default=RDL_TABLE_VERSION)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[str] = mapped_column(String(64), default="CIOS Data Governance")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")
