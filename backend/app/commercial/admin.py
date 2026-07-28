"""Commercial Administration — price guide CSV import/export with version control."""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.commercial.catalog import (
    get_effective_catalog,
    get_runtime_version,
    invalidate_catalog_cache,
    set_runtime_catalog,
)
from app.models.commercial import CommercialCatalogVersion
from app.reference.registry import COMMERCIAL_VERSION, LE_FRAME_COMMISSION_RATE, PRODUCT_CATALOG

VALID_FAMILIES = frozenset({"Master", "Pause", "MediSpa"})

CSV_HEADERS = [
    "product",
    "msrp",
    "selling_price",
    "max_promotion",
    "default_promotion_pct",
    "promo_code",
    "gross_sales",
    "le_frame_incentive",
    "active",
]


def catalog_to_csv_rows(catalog: list[dict] | None = None) -> str:
    rows = catalog or list(PRODUCT_CATALOG)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_HEADERS, extrasaction="ignore")
    writer.writeheader()
    for product in rows:
        default_pct = product.get("default_promotion_pct")
        writer.writerow(
            {
                "product": product.get("code"),
                "msrp": product.get("msrp"),
                "selling_price": product.get("selling_price"),
                "max_promotion": product.get("max_promotion"),
                "default_promotion_pct": default_pct,
                "promo_code": product.get("promo_code") or "",
                "gross_sales": product.get("gross_sales"),
                "le_frame_incentive": product.get("le_frame_incentive"),
                "active": product.get("active", True),
            }
        )
    return buffer.getvalue()


def _registry_lookup(code: str) -> dict | None:
    return next((p for p in PRODUCT_CATALOG if p["code"] == code), None)


def _coerce_promo_pct(value: object) -> float | None:
    if value is None or value == "":
        return None
    pct = float(value)
    if pct > 1:
        pct = pct / 100.0
    return round(pct, 4) if pct > 0 else None


def _post_promo_price(product: dict) -> float:
    """Gross after standing promo: list/gross_sales × (1 − promo%). Alias of catalog Gross."""
    gross = float(product.get("gross_sales") or product.get("selling_price") or 0)
    promo_code = product.get("promo_code")
    pct = product.get("default_promotion_pct")
    if promo_code and pct and float(pct) > 0:
        return round(gross * (1.0 - float(pct)), 2)
    return round(gross, 2)


def normalize_product_record(raw: dict, *, existing: dict | None = None) -> dict:
    """Normalize a single SKU row from admin JSON or CSV import."""
    seed = existing or _registry_lookup(str(raw.get("code") or "").strip()) or {}
    code = str(raw.get("code") or seed.get("code") or "").strip()
    promo_code = (raw.get("promo_code") or seed.get("promo_code") or None) or None
    if isinstance(promo_code, str):
        promo_code = promo_code.strip() or None
    default_pct = _coerce_promo_pct(raw.get("default_promotion_pct", seed.get("default_promotion_pct")))
    if not promo_code:
        default_pct = None

    gross_sales = raw.get("gross_sales", raw.get("selling_price", seed.get("gross_sales")))
    gross_sales = float(gross_sales or 0)
    selling_price = float(raw.get("selling_price", gross_sales or seed.get("selling_price") or 0) or 0)
    if gross_sales <= 0 and selling_price > 0:
        gross_sales = selling_price

    active_raw = raw.get("active", seed.get("active", True))
    if isinstance(active_raw, str):
        active = active_raw.strip().lower() not in {"false", "0", "no", "inactive"}
    else:
        active = bool(active_raw)

    ceragem_cogs = raw.get("ceragem_cogs", seed.get("ceragem_cogs"))
    ceragem_cogs = float(ceragem_cogs) if ceragem_cogs not in (None, "") else None

    record = {
        "code": code,
        "name": str(raw.get("name") or seed.get("name") or code).strip(),
        "family": str(raw.get("family") or seed.get("family") or "Master").strip(),
        "category": str(raw.get("category") or seed.get("category") or "Core").strip(),
        "msrp": float(raw.get("msrp", seed.get("msrp", 0)) or 0),
        "selling_price": selling_price,
        "max_promotion": float(raw.get("max_promotion", seed.get("max_promotion", 0)) or 0),
        "gross_sales": gross_sales,
        "default_promotion_pct": default_pct,
        "promo_code": promo_code,
        "ceragem_cogs": ceragem_cogs,
        "segment": str(raw.get("segment") or seed.get("segment") or "Wellness").strip(),
        "order": int(raw.get("order", seed.get("order", 50)) or 50),
        "active": active,
    }
    # LE Frame Incentive is always Gross × 15% (standing post-promo Gross)
    record["le_frame_incentive"] = round(_post_promo_price(record) * float(LE_FRAME_COMMISSION_RATE), 2)
    return record


def validate_catalog_products(products: list[dict]) -> tuple[list[dict], list[str]]:
    """Validate and normalize SKU catalog rows from admin UI."""
    if not products:
        return [], ["At least one SKU is required"]

    catalog: list[dict] = []
    errors: list[str] = []
    seen: set[str] = set()

    for index, raw in enumerate(products, start=1):
        code = str(raw.get("code") or "").strip()
        if not code:
            errors.append(f"Row {index}: missing SKU code")
            continue
        if code == "Pause S4":
            errors.append(f"Row {index}: use Master S4 instead of legacy Pause S4")
            continue
        if code in seen:
            errors.append(f"Row {index}: duplicate SKU '{code}'")
            continue
        seen.add(code)

        existing = _registry_lookup(code)
        product = normalize_product_record(raw, existing=existing)
        if product["msrp"] <= 0:
            errors.append(f"Row {index} ({code}): MSRP must be greater than zero")
        if product["gross_sales"] <= 0:
            errors.append(f"Row {index} ({code}): gross sales must be greater than zero")
        if product["family"] not in VALID_FAMILIES:
            errors.append(f"Row {index} ({code}): family must be Master, Pause, or MediSpa")
        if product["promo_code"] and not product["default_promotion_pct"]:
            errors.append(f"Row {index} ({code}): promotion percent required when promo code is set")
        if product["default_promotion_pct"] and not product["promo_code"]:
            errors.append(f"Row {index} ({code}): promo code required when promotion percent is set")
        catalog.append(product)

    if errors:
        return [], errors
    catalog.sort(key=lambda row: (not row.get("active", True), int(row.get("order") or 50), row["code"]))
    return catalog, []


def enrich_catalog_product(product: dict) -> dict:
    enriched = dict(product)
    # Catalog Gross = MSRP − Promo (standing promo applied to list). Keep post_promo_price for API compat.
    gross = _post_promo_price(product)
    enriched["post_promo_price"] = gross
    enriched["gross"] = gross

    # LE Frame Incentive = Gross × 15%
    le = round(gross * float(LE_FRAME_COMMISSION_RATE), 2)
    enriched["le_frame_incentive"] = le
    cogs_raw = product.get("ceragem_cogs")
    if cogs_raw is not None and cogs_raw != "":
        cogs = float(cogs_raw)
        # Net Profit = MSRP − Promo − LE Frame Incentive − COGS (= Gross − LE − COGS)
        net_profit = round(gross - le - cogs, 2)
        enriched["net_profit"] = net_profit
        margin_base = gross - le
        enriched["net_profit_pct"] = round(net_profit / margin_base, 4) if margin_base > 0 else None
    else:
        enriched["net_profit"] = None
        enriched["net_profit_pct"] = None

    pct = product.get("default_promotion_pct")
    enriched["default_promotion_pct_display"] = round(float(pct) * 100, 1) if pct else None
    return enriched


def get_catalog_snapshot(db: Session) -> dict:
    """Current effective catalog for admin UI."""
    published_row = (
        db.query(CommercialCatalogVersion)
        .filter(CommercialCatalogVersion.status == "published")
        .order_by(CommercialCatalogVersion.approved_at.desc(), CommercialCatalogVersion.created_at.desc())
        .first()
    )
    products = [enrich_catalog_product(p) for p in get_effective_catalog()]
    products.sort(key=lambda row: (not row.get("active", True), int(row.get("order") or 50), row["code"]))
    draft_rows = (
        db.query(CommercialCatalogVersion)
        .filter(CommercialCatalogVersion.status == "draft")
        .order_by(CommercialCatalogVersion.created_at.desc())
        .limit(5)
        .all()
    )
    return {
        "version": get_runtime_version(),
        "source": "published_db" if published_row else "registry_default",
        "published_version_id": str(published_row.id) if published_row else None,
        "active_sku_count": sum(1 for p in products if p.get("active", True)),
        "products": products,
        "draft_versions": [
            {
                "id": str(row.id),
                "version": row.version,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "sku_count": len(json.loads(row.catalog_json)) if row.catalog_json else 0,
            }
            for row in draft_rows
        ],
    }


def save_catalog(
    db: Session,
    products: list[dict],
    *,
    created_by: str | None = None,
    notes: str | None = None,
    publish: bool = False,
) -> dict:
    """Save SKU catalog from admin UI — optional immediate publish to runtime."""
    catalog, errors = validate_catalog_products(products)
    if errors:
        return {"ok": False, "errors": errors}

    version_name = f"{COMMERCIAL_VERSION}-admin-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    row = CommercialCatalogVersion(
        version=version_name,
        catalog_json=json.dumps(catalog),
        status="draft",
        created_by=created_by,
        notes=notes or "SKU catalog admin save",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    if publish:
        result = approve_catalog_version(db, str(row.id), approved_by=created_by)
        result["version_id"] = str(row.id)
        return result

    return {
        "ok": True,
        "version_id": str(row.id),
        "version": version_name,
        "status": "draft",
        "sku_count": len(catalog),
        "published": False,
    }


def parse_catalog_csv(content: str) -> tuple[list[dict], list[str]]:
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV is empty or missing headers")

    normalized_headers = {h.strip().lower().replace(" ", "_"): h for h in reader.fieldnames}
    product_key = normalized_headers.get("product") or normalized_headers.get("product_code") or normalized_headers.get("code")
    if not product_key:
        raise ValueError("CSV must include a 'product' column")

    catalog: list[dict] = []
    errors: list[str] = []
    seen: set[str] = set()

    for line_no, row in enumerate(reader, start=2):
        raw = {k.strip().lower().replace(" ", "_"): (v or "").strip() for k, v in row.items()}
        code = raw.get("product") or raw.get("product_code") or raw.get("code")
        if not code:
            errors.append(f"Line {line_no}: missing product code")
            continue
        if code in seen:
            errors.append(f"Line {line_no}: duplicate product '{code}'")
            continue
        seen.add(code)

        def _float(key: str, default: float | None = None) -> float | None:
            val = raw.get(key, "")
            if val == "":
                return default
            try:
                return float(val)
            except ValueError:
                errors.append(f"Line {line_no}: invalid number for {key}")
                return default

        existing = next((p for p in PRODUCT_CATALOG if p["code"] == code), None)
        default_pct = _float("default_promotion_pct")
        active_raw = raw.get("active", "true").lower()
        active = active_raw not in {"false", "0", "no", "inactive"}

        row = {
            "code": code,
            "name": (existing or {}).get("name", code),
            "family": (existing or {}).get("family", "Master"),
            "category": (existing or {}).get("category", "Core"),
            "msrp": _float("msrp", (existing or {}).get("msrp", 0.0)) or 0.0,
            "selling_price": _float("selling_price", (existing or {}).get("selling_price")),
            "max_promotion": _float("max_promotion", (existing or {}).get("max_promotion", 0.0)) or 0.0,
            "gross_sales": _float("gross_sales", _float("selling_price")),
            "default_promotion_pct": default_pct,
            "promo_code": raw.get("promo_code") or None,
            "segment": (existing or {}).get("segment", "Wellness"),
            "order": (existing or {}).get("order", 50),
            "active": active,
            "ceragem_cogs": (existing or {}).get("ceragem_cogs"),
        }
        row["le_frame_incentive"] = round(_post_promo_price(row) * float(LE_FRAME_COMMISSION_RATE), 2)
        catalog.append(row)

    if errors:
        return [], errors
    if not catalog:
        return [], ["No product rows found in CSV"]
    return catalog, []


def list_catalog_versions(db: Session, limit: int = 20) -> list[dict]:
    rows = (
        db.query(CommercialCatalogVersion)
        .order_by(CommercialCatalogVersion.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(row.id),
            "version": row.version,
            "status": row.status,
            "created_by": row.created_by,
            "approved_by": row.approved_by,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "approved_at": row.approved_at.isoformat() if row.approved_at else None,
            "notes": row.notes,
            "sku_count": len(json.loads(row.catalog_json)) if row.catalog_json else 0,
        }
        for row in rows
    ]


def import_catalog_csv(
    db: Session,
    content: str,
    *,
    version: str | None = None,
    created_by: str | None = None,
    notes: str | None = None,
) -> dict:
    catalog, errors = parse_catalog_csv(content)
    if errors:
        return {"ok": False, "errors": errors}

    version_name = version or f"{COMMERCIAL_VERSION}-draft-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    row = CommercialCatalogVersion(
        version=version_name,
        catalog_json=json.dumps(catalog),
        status="draft",
        created_by=created_by,
        notes=notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "ok": True,
        "version_id": str(row.id),
        "version": version_name,
        "status": "draft",
        "sku_count": len(catalog),
    }


def approve_catalog_version(db: Session, version_id: str, approved_by: str | None = None) -> dict:
    from app.cache.dashboard_cache import invalidate_dashboard_cache

    row = db.query(CommercialCatalogVersion).filter(CommercialCatalogVersion.id == uuid.UUID(version_id)).first()
    if not row:
        raise ValueError("Version not found")

    (
        db.query(CommercialCatalogVersion)
        .filter(CommercialCatalogVersion.status == "published")
        .update({"status": "archived"}, synchronize_session=False)
    )

    row.status = "published"
    row.approved_by = approved_by
    row.approved_at = datetime.utcnow()
    db.commit()

    catalog = json.loads(row.catalog_json)
    set_runtime_catalog(catalog, row.version)
    invalidate_catalog_cache()
    set_runtime_catalog(catalog, row.version)
    invalidate_dashboard_cache()

    return {
        "ok": True,
        "version": row.version,
        "status": "published",
        "sku_count": len(catalog),
        "published": True,
    }


def rollback_catalog_version(db: Session, version_id: str, approved_by: str | None = None) -> dict:
    return approve_catalog_version(db, version_id, approved_by=approved_by)
