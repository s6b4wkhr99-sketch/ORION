"""Runtime promotion policy tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.commercial.catalog import set_runtime_catalog
from app.commercial.promotion_policy import (
    active_promotion_order,
    build_active_promotion_rows,
    is_promotion_active,
    promotion_pct,
)
from app.reference.registry import PRODUCT_CATALOG


def _catalog_without_promo(product_code: str) -> list[dict]:
    catalog = [dict(p) for p in PRODUCT_CATALOG if p.get("active", True)]
    for product in catalog:
        if product["code"] == product_code:
            product["promo_code"] = None
            product["default_promotion_pct"] = None
    return catalog


def test_active_promotions_follow_runtime_catalog():
    assert is_promotion_active("Master V6")
    assert promotion_pct("Master S4") == 0.30


def test_pause_s4_legacy_name_resolves_promo_on_master_s4():
    assert is_promotion_active("Pause S4")
    assert promotion_pct("Pause S4") == 0.30
    assert len(build_active_promotion_rows()) == len(active_promotion_order())


def test_inactive_promo_sku_is_not_active():
    set_runtime_catalog(_catalog_without_promo("Pause M6s"), "test-no-m6s-promo")
    assert not is_promotion_active("Pause M6s")
    assert promotion_pct("Pause M6s") == 0.0
    assert "Pause M6s" not in active_promotion_order()
