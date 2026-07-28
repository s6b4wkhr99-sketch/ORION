"""Commercial catalog admin — validation and publish."""

from __future__ import annotations

import pytest

from app.commercial.admin import enrich_catalog_product, normalize_product_record, save_catalog, validate_catalog_products
from app.commercial.catalog import get_effective_catalog
from app.database import Base, SessionLocal, engine
from app.models.commercial import CommercialCatalogVersion
from app.reference.registry import PRODUCT_CATALOG


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.query(CommercialCatalogVersion).delete()
        session.commit()
        session.close()


def test_validate_catalog_products_accepts_registry_defaults():
    products, errors = validate_catalog_products([dict(p) for p in PRODUCT_CATALOG if p.get("active", True)])
    assert not errors
    assert len(products) == 9
    assert products[0]["code"]


def test_validate_catalog_products_rejects_duplicate_and_missing_code():
    base = dict(PRODUCT_CATALOG[0])
    _, errors = validate_catalog_products([base, base])
    assert any("duplicate" in err.lower() for err in errors)

    _, errors = validate_catalog_products([{"name": "No Code", "msrp": 100, "gross_sales": 100}])
    assert any("missing sku code" in err.lower() for err in errors)


def test_normalize_product_record_promo_pct_from_percent_input():
    product = normalize_product_record(
        {
            "code": "Master V6",
            "msrp": 7999,
            "gross_sales": 6399,
            "promo_code": "SAVE20",
            "default_promotion_pct": 20,
        }
    )
    assert product["default_promotion_pct"] == 0.2
    assert enrich_catalog_product(product)["post_promo_price"] == 5119.2
    assert enrich_catalog_product(product)["gross"] == 5119.2
    # LE = Gross × 15%; Net Profit = Gross − LE − COGS; NP% = NP / (Gross − LE)
    enriched = enrich_catalog_product(product)
    assert enriched["le_frame_incentive"] == round(5119.2 * 0.15, 2)
    assert enriched["net_profit"] == round(5119.2 - enriched["le_frame_incentive"] - 2980, 2)
    assert enriched["net_profit_pct"] == round(
        enriched["net_profit"] / (5119.2 - enriched["le_frame_incentive"]),
        4,
    )


def test_save_and_publish_updates_runtime_catalog(db):
    catalog = [dict(p) for p in PRODUCT_CATALOG if p.get("active", True)]
    catalog[0] = {**catalog[0], "gross_sales": 8299.0, "selling_price": 8299.0}

    result = save_catalog(db, catalog, created_by="admin@test.com", publish=True)
    assert result["ok"] is True
    assert result["published"] is True

    live = get_effective_catalog()
    v9 = next(row for row in live if row["code"] == "Master V9")
    assert v9["gross_sales"] == 8299.0


def test_save_draft_does_not_publish(db):
    catalog = [dict(p) for p in PRODUCT_CATALOG if p.get("active", True)]
    result = save_catalog(db, catalog, created_by="admin@test.com", publish=False)
    assert result["ok"] is True
    assert result.get("published") is False
    assert result["status"] == "draft"
