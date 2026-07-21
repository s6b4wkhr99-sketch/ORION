"""Runtime commercial catalog — published DB versions override registry defaults."""

from __future__ import annotations

import json
import logging
from copy import deepcopy

from sqlalchemy.orm import Session

from app.reference.registry import COMMERCIAL_VERSION, PRODUCT_CATALOG

logger = logging.getLogger("cios.commercial.catalog")

_runtime_catalog: list[dict] | None = None
_runtime_version: str = COMMERCIAL_VERSION


def consolidate_catalog_skus(catalog: list[dict]) -> list[dict]:
    """Master S4 is the single SSOT — merge legacy Pause S4 promo row into Master S4."""
    by_code: dict[str, dict] = {}
    for product in catalog:
        code = str(product.get("code") or "").strip()
        if not code or code == "Pause S4":
            legacy = deepcopy(product)
            master = by_code.get("Master S4")
            if master is None:
                legacy["code"] = "Master S4"
                legacy["name"] = "Master S4"
                legacy["family"] = "Master"
                legacy["active"] = True
                by_code["Master S4"] = legacy
            else:
                if legacy.get("promo_code") and not master.get("promo_code"):
                    master["promo_code"] = legacy.get("promo_code")
                    master["default_promotion_pct"] = legacy.get("default_promotion_pct")
                    master["max_promotion"] = legacy.get("max_promotion", master.get("max_promotion"))
            continue
        by_code[code] = deepcopy(product)
    return list(by_code.values())


def normalize_catalog_promotions(catalog: list[dict]) -> list[dict]:
    """Preserve promo fields from catalog JSON only — promos are runtime-variable."""
    patched = consolidate_catalog_skus(catalog)
    for product in patched:
        if not product.get("promo_code"):
            product["default_promotion_pct"] = None
    return patched


def apply_standing_promotion_policy(catalog: list[dict]) -> list[dict]:
    """Backward-compatible alias for catalog normalization."""
    return normalize_catalog_promotions(catalog)


def invalidate_catalog_cache() -> None:
    global _runtime_catalog
    _runtime_catalog = None


def get_runtime_version() -> str:
    return _runtime_version


def set_runtime_catalog(catalog: list[dict], version: str) -> None:
    global _runtime_catalog, _runtime_version
    _runtime_catalog = normalize_catalog_promotions(catalog)
    _runtime_version = version
    logger.info("Commercial catalog runtime updated to v%s (%d SKUs)", version, len(catalog))


def get_effective_catalog() -> list[dict]:
    raw = _runtime_catalog if _runtime_catalog is not None else list(PRODUCT_CATALOG)
    return normalize_catalog_promotions(raw)


def active_products() -> list[dict]:
    return [p for p in get_effective_catalog() if p.get("active", True)]


def product_by_code(code: str) -> dict | None:
    for product in get_effective_catalog():
        if product.get("code") == code:
            return product
    return None


def load_published_catalog(db: Session) -> tuple[list[dict], str]:
    from app.models.commercial import CommercialCatalogVersion

    row = (
        db.query(CommercialCatalogVersion)
        .filter(CommercialCatalogVersion.status == "published")
        .order_by(CommercialCatalogVersion.approved_at.desc(), CommercialCatalogVersion.created_at.desc())
        .first()
    )
    if row is None:
        return normalize_catalog_promotions(list(PRODUCT_CATALOG)), COMMERCIAL_VERSION
    try:
        catalog = json.loads(row.catalog_json)
    except json.JSONDecodeError:
        logger.warning("Invalid catalog JSON for version %s — using registry", row.version)
        return normalize_catalog_promotions(list(PRODUCT_CATALOG)), COMMERCIAL_VERSION
    return normalize_catalog_promotions(catalog), row.version


def warm_catalog_cache(db: Session) -> None:
    catalog, version = load_published_catalog(db)
    set_runtime_catalog(catalog, version)
