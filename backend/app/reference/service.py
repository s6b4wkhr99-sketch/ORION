"""Volume 22 — Reference Data Library read-only service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.reference_data import (
    CampaignTypeMaster,
    CeragemSegmentMaster,
    DashboardMaster,
    MetricMaster,
    ProductMaster,
    ProviderVersionMaster,
    PurchasePowerMaster,
    PrizmSegmentMaster,
    ReferenceDataVersion,
    StateMaster,
    ZipMaster,
)
from app.reference.registry import RDL_VERSION


def _rows(model, db: Session, order_field: str = "display_order") -> list:
    return db.query(model).order_by(getattr(model, order_field)).all()


def get_reference_version(db: Session) -> dict:
    row = db.query(ReferenceDataVersion).order_by(ReferenceDataVersion.id.desc()).first()
    return {
        "libraryVersion": row.library_version if row else RDL_VERSION,
        "referenceVersion": row.reference_version if row else "1.0",
        "owner": row.owner if row else "CIOS Data Governance",
        "approvalStatus": row.approval_status if row else "approved",
    }


def get_reference_catalog(db: Session) -> dict:
    from app.reference.registry import REFERENCE_DOMAINS

    version = get_reference_version(db)
    counts = {
        "states": db.query(StateMaster).count(),
        "zips": db.query(ZipMaster).count(),
        "products": db.query(ProductMaster).count(),
        "campaignTypes": db.query(CampaignTypeMaster).count(),
        "ceragemSegments": db.query(CeragemSegmentMaster).count(),
        "prizmSegments": db.query(PrizmSegmentMaster).count(),
        "purchasePowerLevels": db.query(PurchasePowerMaster).count(),
        "providers": db.query(ProviderVersionMaster).count(),
        "dashboards": db.query(DashboardMaster).count(),
        "metrics": db.query(MetricMaster).count(),
    }
    return {"version": version, "domains": list(REFERENCE_DOMAINS), "counts": counts}


def get_products(db: Session, active_only: bool = True) -> list[dict]:
    from app.reference.registry import (
        LE_FRAME_INCENTIVE_BY_SKU,
        PRODUCT_GROSS_SALES,
        PRODUCT_MAX_PROMOTION,
    )

    q = db.query(ProductMaster).order_by(ProductMaster.display_order)
    if active_only:
        q = q.filter(ProductMaster.status == "active")
    return [
        {
            "productCode": p.product_code,
            "productName": p.product_name,
            "productFamily": p.product_family,
            "category": p.category,
            "msrp": p.msrp,
            "maxPromotion": PRODUCT_MAX_PROMOTION.get(p.product_code),
            "grossSales": PRODUCT_GROSS_SALES.get(p.product_code),
            "leFrameIncentive": LE_FRAME_INCENTIVE_BY_SKU.get(p.product_code),
            "targetSegment": p.target_segment,
            "displayOrder": p.display_order,
            "status": p.status,
        }
        for p in q.all()
    ]


def get_product_codes(db: Session) -> tuple[str, ...]:
    return tuple(p["productCode"] for p in get_products(db))


def get_product_prices(db: Session) -> dict[str, float]:
    return {p["productCode"]: float(p["msrp"] or 0) for p in get_products(db, active_only=False)}


def get_supported_products(db: Session) -> tuple[str, ...]:
    products = get_products(db)
    return tuple(
        p["productCode"] for p in products
        if p["productFamily"] in {"Master", "Pause"}
    )


def get_purchase_power_levels(db: Session) -> tuple[str, ...]:
    rows = _rows(PurchasePowerMaster, db)
    return tuple(r.code for r in rows)


def get_level_to_index(db: Session) -> dict[str, float]:
    rows = _rows(PurchasePowerMaster, db)
    return {r.code: float(r.index_score) for r in rows}


def get_ceragem_segments(db: Session) -> tuple[str, ...]:
    rows = _rows(CeragemSegmentMaster, db, "display_order")
    return tuple(r.segment_name for r in rows)


def get_ceragem_v19_map(db: Session) -> dict[str, str]:
    from app.reference.registry import CERAGEM_V19_MAP

    mapping = dict(CERAGEM_V19_MAP)
    for r in _rows(CeragemSegmentMaster, db, "display_order"):
        if r.legacy_v04_segment:
            mapping[r.legacy_v04_segment] = r.segment_name
    return mapping


def get_prizm_segments(db: Session) -> list[str]:
    rows = _rows(PrizmSegmentMaster, db, "display_order")
    return [r.segment_name for r in rows]


def get_audience_segments() -> list[dict]:
    from app.reference.sfmc_audience_segments import SFMC_AUDIENCE_SEGMENTS

    return [
        {
            "segmentId": s.segment_id,
            "segmentCode": s.segment_code,
            "segmentName": s.segment_name,
            "ciosKey": s.cios_key,
            "ciosLabel": s.cios_label,
            "channelMix": s.channel_mix,
            "audienceTier": s.audience_tier,
            "campaignPriority": s.campaign_priority,
            "campaignTypes": list(s.campaign_types),
            "description": s.description,
        }
        for s in SFMC_AUDIENCE_SEGMENTS
    ]


def get_campaign_types(db: Session) -> tuple[str, ...]:
    rows = _rows(CampaignTypeMaster, db)
    return tuple(r.code for r in rows)


def get_providers(db: Session) -> tuple[str, ...]:
    rows = db.query(ProviderVersionMaster).order_by(ProviderVersionMaster.provider_name).all()
    return tuple(r.provider_name for r in rows)


def get_dashboard_config(db: Session) -> dict:
    dashboards = [
        {"code": d.code, "name": d.name, "displayOrder": d.display_order}
        for d in _rows(DashboardMaster, db)
    ]
    metrics = [
        {"code": m.code, "name": m.name, "type": m.metric_type, "displayOrder": m.display_order}
        for m in _rows(MetricMaster, db)
    ]
    return {"dashboards": dashboards, "metrics": metrics}


def get_geographic_summary(db: Session) -> dict:
    return {
        "stateCount": db.query(StateMaster).count(),
        "zipCount": db.query(ZipMaster).count(),
        "states": [
            {"code": s.state_code, "name": s.state_name, "region": s.region, "timeZone": s.time_zone}
            for s in db.query(StateMaster).order_by(StateMaster.state_code).limit(10).all()
        ],
    }
