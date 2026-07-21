"""Seed field_mapping and export_template from data dictionary — Volume 09 / 15 SSOT."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.mapping.seed_rfc import seed_auto_mapping
from app.reference.seed import seed_reference_data, sync_product_catalog
from app.mapping.data_dictionary import (
    DICTIONARY_VERSION,
    EXPORT_PROVIDER_MAPPINGS,
    UPLOAD_SOURCE_MAPPINGS,
)
from app.models.export import ExportTemplate
from app.models.mapping import FieldMapping
from app.models.provider_mapping import ProviderMappingVersion
from app.models.zip import ZipIntelligence
from app.providers.config import PROVIDER_EXPORT_EXTENSIONS
from app.providers.constants import COMPATIBILITY_VERSION, PROVIDER_MAPPING_VERSION, SUPPORTED_PROVIDERS

ZIP_INTELLIGENCE_SEED: list[tuple[str, str, str, float, bool, int, str]] = [
    ("06830", "Greenwich", "CT", 182000.0, True, 61171, "Fairfield"),
    ("06901", "Stamford", "CT", 95000.0, True, 135470, "Fairfield"),
    ("06604", "Bridgeport", "CT", 52000.0, False, 148654, "Fairfield"),
    ("06103", "Hartford", "CT", 48000.0, False, 121054, "Hartford"),
    ("06510", "New Haven", "CT", 55000.0, False, 134708, "New Haven"),
    ("06801", "Bethel", "CT", 98000.0, False, 10000, "Fairfield"),
    ("06405", "Branford", "CT", 88000.0, False, 28000, "New Haven"),
    ("06001", "Avon", "CT", 115000.0, True, 19000, "Hartford"),
    ("06457", "Middletown", "CT", 72000.0, False, 47000, "Middlesex"),
    ("06708", "Waterbury", "CT", 46000.0, False, 110000, "New Haven"),
    ("06702", "Waterbury", "CT", 47000.0, False, 45000, "New Haven"),
    ("06851", "Norwalk", "CT", 102000.0, True, 91000, "Fairfield"),
    ("06810", "Danbury", "CT", 78000.0, False, 86000, "Fairfield"),
    ("06824", "Fairfield", "CT", 125000.0, True, 62000, "Fairfield"),
    ("06880", "Westport", "CT", 175000.0, True, 28000, "Fairfield"),
]


def _seed_field_mappings(db: Session) -> None:
    version_count = db.query(FieldMapping).filter(FieldMapping.version == DICTIONARY_VERSION).count()
    if version_count > 0:
        return
    db.query(FieldMapping).delete()
    for source, target, dtype, required in UPLOAD_SOURCE_MAPPINGS:
        db.add(FieldMapping(
            source_field=source,
            target_field=target,
            data_type=dtype,
            required=required,
            version=DICTIONARY_VERSION,
        ))


def _seed_export_templates(db: Session) -> None:
    stale = db.query(ExportTemplate).filter(ExportTemplate.field.in_(["email", "zip", "permission"])).count()
    if stale == 0 and db.query(ExportTemplate).count() > 0:
        return
    db.query(ExportTemplate).delete()
    seen: set[tuple[str, str]] = set()
    for provider, field, target_name, order, required in EXPORT_PROVIDER_MAPPINGS + PROVIDER_EXPORT_EXTENSIONS:
        key = (provider, field)
        if key in seen:
            continue
        seen.add(key)
        db.add(ExportTemplate(
            provider=provider,
            field=field,
            target_name=target_name,
            order=order,
            required=required,
        ))


def _seed_provider_mapping_versions(db: Session) -> None:
    if db.query(ProviderMappingVersion).count() >= len(SUPPORTED_PROVIDERS):
        return
    now = datetime.utcnow()
    for name in SUPPORTED_PROVIDERS:
        if db.query(ProviderMappingVersion).filter(ProviderMappingVersion.provider_name == name).first():
            continue
        db.add(
            ProviderMappingVersion(
                provider_name=name,
                version=PROVIDER_MAPPING_VERSION,
                created_date=now,
                modified_date=now,
                owner="CIOS Integration Team",
                compatibility_version=COMPATIBILITY_VERSION,
                status="active",
            )
        )


def seed_configuration(db: Session) -> None:
    _seed_field_mappings(db)
    seed_auto_mapping(db)
    seed_reference_data(db)
    sync_product_catalog(db)

    _seed_export_templates(db)
    _seed_provider_mapping_versions(db)

    if db.query(ZipIntelligence).count() == 0:
        for zip_code, city, state, median, top50, population, county in ZIP_INTELLIGENCE_SEED:
            db.add(ZipIntelligence(
                zip=zip_code,
                city=city,
                state=state,
                median_income=median,
                top50_rank=top50,
                population=population,
                county=county,
            ))

    db.commit()
