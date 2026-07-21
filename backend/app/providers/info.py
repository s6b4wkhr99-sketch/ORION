"""Volume 15 — Provider metadata for API consumers."""

from sqlalchemy.orm import Session

from app.models.provider_mapping import ProviderMappingVersion
from app.providers.config import PROVIDER_METADATA
from app.providers.constants import SUPPORTED_PROVIDERS


def list_providers(db: Session) -> list[dict]:
    versions = {v.provider_name: v for v in db.query(ProviderMappingVersion).all()}
    result = []
    for name in SUPPORTED_PROVIDERS:
        meta = PROVIDER_METADATA.get(name, {})
        ver = versions.get(name)
        result.append(
            {
                "providerName": name,
                "exportFormat": meta.get("exportFormat", "CSV"),
                "encoding": meta.get("encoding", "UTF-8"),
                "delimiter": meta.get("delimiter", ","),
                "primaryIdentifier": meta.get("primaryIdentifier"),
                "exportRequiredFields": meta.get("exportRequiredFields", []),
                "importMetrics": meta.get("importMetrics", []),
                "mappingVersion": {
                    "version": ver.version if ver else "1.0.0",
                    "createdDate": ver.created_date.isoformat() if ver and ver.created_date else None,
                    "modifiedDate": ver.modified_date.isoformat() if ver and ver.modified_date else None,
                    "owner": ver.owner if ver else "CIOS Integration Team",
                    "compatibilityVersion": ver.compatibility_version if ver else "CIOS 1.0",
                    "status": ver.status if ver else "active",
                },
            }
        )
    return result


def get_provider(db: Session, provider_name: str) -> dict | None:
    for item in list_providers(db):
        if item["providerName"] == provider_name:
            return item
    return None
