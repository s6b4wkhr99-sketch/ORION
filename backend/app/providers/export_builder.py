"""Volume 15 — Shared export CSV building (mapping layer only)."""

from app.commercial.catalog import product_by_code
from app.commercial.engine import cap_promotion, default_promotion_amount
from app.mapping.data_dictionary import EXPORT_VALUE_RESOLVERS, INTELLIGENCE_EXPORT_FIELDS
from app.models.customer import Customer, CustomerIntelligence
from app.models.export import ExportTemplate
from app.reference.registry import ACTIVE_STANDING_PROMOTIONS
from sqlalchemy.orm import Session


def get_export_headers(db: Session, provider: str) -> list[tuple[str, str]]:
    templates = (
        db.query(ExportTemplate)
        .filter(ExportTemplate.provider == provider)
        .order_by(ExportTemplate.order)
        .all()
    )
    if not templates:
        templates = (
            db.query(ExportTemplate)
            .filter(ExportTemplate.provider == "Generic CSV")
            .order_by(ExportTemplate.order)
            .all()
        )
    headers = [(t.field, t.target_name) for t in templates]
    for field, label in INTELLIGENCE_EXPORT_FIELDS:
        headers.append((f"intel_{field}", label))
    headers.extend([
        ("promo_code", "Promo Code"),
        ("recommended_promotion", "Recommended Promotion"),
        ("price_resistance_score", "Price Resistance Score"),
        ("commercial_version", "Commercial Version"),
        ("campaign_id", "Campaign ID"),
        ("campaign_name", "Campaign Name"),
    ])
    return headers


def resolve_export_value(field: str, customer: Customer, intel: CustomerIntelligence) -> str:
    if field == "promo_code":
        if intel.promo_code:
            return intel.promo_code
        product = intel.recommended_product or "Master S4"
        standing = ACTIVE_STANDING_PROMOTIONS.get(product)
        if standing:
            return str(standing["promo_code"])
        return ""
    if field == "recommended_promotion":
        if intel.recommended_promotion is not None:
            return str(intel.recommended_promotion)
        product = intel.recommended_product
        if not product:
            return ""
        proposed = default_promotion_amount(product)
        return str(cap_promotion(product, proposed)["recommended_promotion"])
    if field == "price_resistance_score":
        return str(intel.price_resistance_score or "")
    if field == "commercial_version":
        return str(intel.commercial_version or "")
    if field in {"campaign_id", "campaign_name"}:
        return ""
    resolver = EXPORT_VALUE_RESOLVERS.get(field)
    if resolver:
        return resolver(customer, intel)
    return ""
