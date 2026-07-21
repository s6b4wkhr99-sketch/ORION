"""Volume 22 — Reference Data Library seed."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.reference_data import (
    CampaignStatusMaster,
    CampaignTypeMaster,
    CeragemSegmentMaster,
    ChartTypeMaster,
    CountryMaster,
    CurrencyMaster,
    DashboardMaster,
    DwellingMaster,
    GenderMaster,
    GenerationMaster,
    HolidayMaster,
    HouseholdMaster,
    IncomeRangeMaster,
    LanguageMaster,
    LifestyleMaster,
    MessageTypeMaster,
    MetricMaster,
    PainIndexMaster,
    PriorityMaster,
    ProductMaster,
    ProviderStatusMaster,
    ProviderVersionMaster,
    PurchasePowerMaster,
    PrizmSegmentMaster,
    ReferenceDataVersion,
    StateMaster,
    StatusMaster,
    TimeZoneMaster,
    ZipMaster,
)
from app.providers.constants import COMPATIBILITY_VERSION, PROVIDER_MAPPING_VERSION
from app.reference.registry import (
    CAMPAIGN_STATUSES,
    CAMPAIGN_TYPES,
    CERAGEM_SEGMENT_V19,
    CHART_TYPES,
    COUNTRIES,
    CURRENCIES,
    DASHBOARD_DEFINITIONS,
    DWELLING_VALUES,
    GENDER_VALUES,
    GENERATION_VALUES,
    HOLIDAYS,
    HOUSEHOLD_VALUES,
    INCOME_RANGE_VALUES,
    INDEX_LEVELS,
    LANGUAGES,
    LIFESTYLE_LEVELS,
    MESSAGE_TYPES,
    METRIC_DEFINITIONS,
    PAIN_INDEX_LEVELS,
    PRIORITY_LEVELS,
    PRODUCT_CATALOG,
    PROVIDER_NAMES,
    PROVIDER_STATUSES,
    PRIZM_SEGMENTS,
    RDL_OWNER,
    RDL_VERSION,
    SYSTEM_STATUSES,
    TIME_ZONES,
    US_STATES,
)


def seed_reference_data(db: Session) -> None:
    if db.query(ReferenceDataVersion).count() > 0:
        return

    now = datetime.utcnow()
    db.add(ReferenceDataVersion(
        library_version=RDL_VERSION,
        owner=RDL_OWNER,
        approval_status="approved",
        created_date=now,
        modified_date=now,
    ))

    for code, name, region, tz in US_STATES:
        db.add(StateMaster(state_code=code, state_name=name, region=region, time_zone=tz, active=True))

    for zone, iana in TIME_ZONES:
        db.add(TimeZoneMaster(zone_name=zone, iana_id=iana))

    for code, name in COUNTRIES:
        db.add(CountryMaster(country_code=code, country_name=name))

    from app.processing.seed import ZIP_INTELLIGENCE_SEED

    for zip_code, city, state, median, top50, population, county in ZIP_INTELLIGENCE_SEED:
        db.add(ZipMaster(
            zip_code=zip_code,
            state_code=state,
            county=county,
            city=city,
            median_income=median,
            population=population,
            top_income_indicator=top50,
        ))

    for code, desc, order in GENDER_VALUES:
        db.add(GenderMaster(code=code, description=desc, display_order=order))
    for code, desc, order in GENERATION_VALUES:
        db.add(GenerationMaster(code=code, description=desc, display_order=order))
    for code, desc, order in HOUSEHOLD_VALUES:
        db.add(HouseholdMaster(code=code, description=desc, display_order=order))
    for code, desc, order in DWELLING_VALUES:
        db.add(DwellingMaster(code=code, description=desc, display_order=order))
    for code, desc, order in INCOME_RANGE_VALUES:
        db.add(IncomeRangeMaster(code=code, description=desc, display_order=order))

    for product in PRODUCT_CATALOG:
        db.add(ProductMaster(
            product_code=product["code"],
            product_name=product["name"],
            product_family=product["family"],
            category=product["category"],
            status="active" if product.get("active", True) else "inactive",
            msrp=product["msrp"],
            target_segment=product["segment"],
            display_order=product["order"],
        ))

    for code, desc, order in CAMPAIGN_TYPES:
        db.add(CampaignTypeMaster(code=code, description=desc, display_order=order))
    for code, desc, order in CAMPAIGN_STATUSES:
        db.add(CampaignStatusMaster(code=code, description=desc, display_order=order))
    for code, desc, order in MESSAGE_TYPES:
        db.add(MessageTypeMaster(code=code, description=desc, display_order=order))
    for code, desc, order in HOLIDAYS:
        db.add(HolidayMaster(code=code, description=desc, display_order=order))

    for code, desc, color, score, order in INDEX_LEVELS:
        db.add(PurchasePowerMaster(code=code, description=desc, color=color, index_score=score, display_order=order))
    for code, desc, color, score, order in PAIN_INDEX_LEVELS:
        db.add(PainIndexMaster(code=code, description=desc, color=color, index_score=score, display_order=order))
    for code, desc, score, order in LIFESTYLE_LEVELS:
        db.add(LifestyleMaster(code=code, description=desc, index_score=score, display_order=order))
    for name, desc, legacy, order in CERAGEM_SEGMENT_V19:
        db.add(CeragemSegmentMaster(segment_name=name, description=desc, legacy_v04_segment=legacy, display_order=order))
    for code, desc, score, order in PRIORITY_LEVELS:
        db.add(PriorityMaster(code=code, description=desc, score=score, display_order=order))
    for name, desc, order in PRIZM_SEGMENTS:
        db.add(PrizmSegmentMaster(segment_name=name, description=desc, display_order=order))

    for name, desc, order in PROVIDER_NAMES:
        db.add(ProviderVersionMaster(
            provider_name=name,
            version=PROVIDER_MAPPING_VERSION,
            compatibility_version=COMPATIBILITY_VERSION,
        ))
    for code, desc, order in PROVIDER_STATUSES:
        db.add(ProviderStatusMaster(code=code, description=desc, display_order=order))

    for code, name, order in DASHBOARD_DEFINITIONS:
        db.add(DashboardMaster(code=code, name=name, display_order=order))
    for code, name, mtype, order in METRIC_DEFINITIONS:
        db.add(MetricMaster(code=code, name=name, metric_type=mtype, display_order=order))
    for code, name, order in CHART_TYPES:
        db.add(ChartTypeMaster(code=code, name=name, display_order=order))

    for code, name, order in LANGUAGES:
        db.add(LanguageMaster(code=code, name=name, display_order=order))
    for code, name, symbol, order in CURRENCIES:
        db.add(CurrencyMaster(code=code, name=name, symbol=symbol, display_order=order))
    for code, desc, order in SYSTEM_STATUSES:
        db.add(StatusMaster(code=code, description=desc, display_order=order))

    db.commit()


def sync_product_catalog(db: Session) -> None:
    """Keep product_master aligned with registry on every startup."""
    from app.reference.registry import PRODUCT_CATALOG

    for product in PRODUCT_CATALOG:
        row = db.query(ProductMaster).filter(ProductMaster.product_code == product["code"]).one_or_none()
        status = "active" if product.get("active", True) else "inactive"
        if row is None:
            db.add(ProductMaster(
                product_code=product["code"],
                product_name=product["name"],
                product_family=product["family"],
                category=product["category"],
                status=status,
                msrp=product["msrp"],
                target_segment=product["segment"],
                display_order=product["order"],
            ))
            continue
        row.product_name = product["name"]
        row.product_family = product["family"]
        row.category = product["category"]
        row.status = status
        row.msrp = product["msrp"]
        row.target_segment = product["segment"]
        row.display_order = product["order"]
        row.modified_date = datetime.utcnow()
    db.commit()
