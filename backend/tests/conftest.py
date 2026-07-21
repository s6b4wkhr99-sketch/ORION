"""Shared pytest fixtures."""

import pytest

from app.commercial.catalog import invalidate_catalog_cache, set_runtime_catalog
from app.reference.registry import COMMERCIAL_VERSION, PRODUCT_CATALOG


@pytest.fixture(autouse=True)
def reset_runtime_commercial_catalog():
    catalog = [dict(p) for p in PRODUCT_CATALOG if p.get("active", True)]
    invalidate_catalog_cache()
    set_runtime_catalog(catalog, COMMERCIAL_VERSION)
    yield
    invalidate_catalog_cache()
    set_runtime_catalog(catalog, COMMERCIAL_VERSION)
