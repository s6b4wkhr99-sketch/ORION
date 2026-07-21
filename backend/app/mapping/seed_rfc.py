"""RFC-001 — Seed field_master, field_alias, provider_template."""

from sqlalchemy.orm import Session

from app.mapping.data_dictionary import ALL_FIELDS, DICTIONARY_VERSION, UPLOAD_SOURCE_MAPPINGS
from app.mapping.rfc_constants import PROVIDER_UPLOAD_HEADERS
from app.models.auto_mapping import FieldAlias, FieldMaster, ProviderUploadTemplate

RFC_EXTRA_ALIASES: list[tuple[str, str, float]] = [
    ("Customer Email", "email_address", 98.0),
    ("E-mail", "email_address", 97.0),
    ("State Code", "state", 97.0),
    ("Province", "state", 96.0),
    ("Postal Code", "zip_code", 97.0),
    ("ZIP Code", "zip_code", 97.0),
    ("Annual Income", "estimated_income", 96.0),
    ("Estimated Household Income", "estimated_income", 95.0),
    ("Income", "estimated_income", 95.0),
    ("Home Price", "home_value", 91.0),
]


def seed_auto_mapping(db: Session) -> None:
    if db.query(FieldMaster).filter(FieldMaster.version == DICTIONARY_VERSION).count() > 0:
        return

    for field in ALL_FIELDS:
        db.add(FieldMaster(
            internal_field=field.name,
            category=field.category.value,
            data_type=field.data_type,
            required=field.required,
            description=field.description,
            version=DICTIONARY_VERSION,
        ))

    seen_aliases: set[tuple[str, str]] = set()
    for source, target, _dtype, _required in UPLOAD_SOURCE_MAPPINGS:
        key = (source.lower(), target)
        if key in seen_aliases:
            continue
        seen_aliases.add(key)
        db.add(FieldAlias(
            alias_header=source,
            internal_field=target,
            match_type="alias",
            confidence=98.0,
            approved=True,
            version=DICTIONARY_VERSION,
        ))

    for alias, target, confidence in RFC_EXTRA_ALIASES:
        key = (alias.lower(), target)
        if key in seen_aliases:
            continue
        seen_aliases.add(key)
        db.add(FieldAlias(
            alias_header=alias,
            internal_field=target,
            match_type="alias",
            confidence=confidence,
            approved=True,
            version=DICTIONARY_VERSION,
        ))

    for template_name, headers in PROVIDER_UPLOAD_HEADERS.items():
        for priority, (source, target) in enumerate(headers, start=1):
            db.add(ProviderUploadTemplate(
                template_name=template_name,
                source_header=source,
                internal_field=target,
                priority=priority,
                version=DICTIONARY_VERSION,
            ))
