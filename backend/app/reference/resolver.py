"""Volume 22 — Reference Data resolver (DB-first with registry fallback)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.reference import registry
from app.reference.service import (
    get_campaign_types,
    get_ceragem_segments,
    get_ceragem_v19_map,
    get_level_to_index,
    get_prizm_segments,
    get_product_codes,
    get_product_prices,
    get_providers,
    get_purchase_power_levels,
    get_supported_products,
)


def purchase_power_levels(db: Session | None = None) -> tuple[str, ...]:
    if db is not None:
        rows = get_purchase_power_levels(db)
        if rows:
            return rows
    return registry.PURCHASE_POWER_LEVELS


def level_to_index(db: Session | None = None) -> dict[str, float]:
    if db is not None:
        mapping = get_level_to_index(db)
        if mapping:
            return mapping
    return dict(registry.LEVEL_TO_INDEX)


def product_codes(db: Session | None = None) -> tuple[str, ...]:
    if db is not None:
        codes = get_product_codes(db)
        if codes:
            return codes
    return registry.PRODUCT_CODES


def supported_products(db: Session | None = None) -> tuple[str, ...]:
    if db is not None:
        products = get_supported_products(db)
        if products:
            return products
    return registry.SUPPORTED_PRODUCTS


def product_prices(db: Session | None = None) -> dict[str, float]:
    if db is not None:
        prices = get_product_prices(db)
        if prices:
            return prices
    return dict(registry.PRODUCT_PRICES)


def ceragem_segments_v19(db: Session | None = None) -> tuple[str, ...]:
    if db is not None:
        segments = get_ceragem_segments(db)
        if segments:
            return segments
    return tuple(s[0] for s in registry.CERAGEM_SEGMENT_V19)


def ceragem_v19_map(db: Session | None = None) -> dict[str, str]:
    if db is not None:
        mapping = get_ceragem_v19_map(db)
        if mapping:
            return mapping
    return {s[2]: s[0] for s in registry.CERAGEM_SEGMENT_V19 if s[2]}


def prizm_segment_list(db: Session | None = None) -> list[str]:
    if db is not None:
        segments = get_prizm_segments(db)
        if segments:
            return segments
    return [s[0] for s in registry.PRIZM_SEGMENTS]


def campaign_type_list(db: Session | None = None) -> tuple[str, ...]:
    if db is not None:
        types = get_campaign_types(db)
        if types:
            return types
    return tuple(t[0] for t in registry.CAMPAIGN_TYPES)


def supported_providers(db: Session | None = None) -> tuple[str, ...]:
    if db is not None:
        providers = get_providers(db)
        if providers:
            return providers
    return tuple(p[0] for p in registry.PROVIDER_NAMES)
