"""Volume 17 Section 16 — Comparative analysis."""

from sqlalchemy.orm import Session

from app.campaign.dashboards import PRODUCTS, get_product_dashboard, get_state_dashboard, get_zip_dashboard
from app.models.campaign import Campaign, CampaignState
from app.models.customer import Customer, CustomerIntelligence


def _campaign_snapshot(db: Session, campaign_id: str) -> dict:
    camp = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
    rows = db.query(CampaignState).filter(CampaignState.campaign_id == campaign_id).all()
    revenue = sum(r.revenue or 0 for r in rows)
    cost = sum(r.cost or 0 for r in rows)
    sent = sum(r.sent for r in rows)
    roi_vals = [r.roi for r in rows if r.roi is not None]
    return {
        "id": campaign_id,
        "name": camp.campaign_name if camp else campaign_id,
        "type": camp.campaign_type if camp else None,
        "provider": camp.provider if camp else None,
        "revenue": round(revenue, 2),
        "cost": round(cost, 2),
        "roi": round(sum(roi_vals) / len(roi_vals), 4) if roi_vals else None,
        "sent": sent,
        "conversion": round(sum(r.conversion or 0 for r in rows) / max(sent, 1), 6),
    }


def _state_snapshot(db: Session, state: str, upload_id: str | None = None) -> dict:
    dash = get_state_dashboard(db, upload_id, state)
    kpis = dash.get("kpis", {})
    return {
        "id": state,
        "target_customers": kpis.get("target_customers"),
        "expected_revenue": kpis.get("expected_revenue"),
        "campaign_roi": kpis.get("campaign_roi"),
        "average_conversion": kpis.get("average_conversion"),
    }


def _zip_snapshot(db: Session, zip_code: str, upload_id: str | None = None) -> dict:
    dash = get_zip_dashboard(db, upload_id, zip_code)
    summary = dash.get("summary", {})
    return {
        "id": zip_code,
        "target_customers": summary.get("target_customers"),
        "expected_revenue": summary.get("expected_revenue"),
        "campaign_priority": summary.get("campaign_priority"),
    }


def _product_snapshot(db: Session, product: str, upload_id: str | None = None) -> dict:
    dash = get_product_dashboard(db, upload_id, product)
    kpis = dash.get("kpis", {})
    return {"id": product, **kpis}


def _segment_snapshot(db: Session, segment: str) -> dict:
    rows = (
        db.query(CustomerIntelligence)
        .filter(CustomerIntelligence.ceragem_segment == segment)
        .all()
    )
    return {
        "id": segment,
        "customers": len(rows),
        "expected_revenue": round(sum(r.expected_revenue or 0 for r in rows), 2),
        "average_conversion": round(sum(r.expected_conversion or 0 for r in rows) / max(len(rows), 1), 6),
    }


def _provider_snapshot(db: Session, provider: str) -> dict:
    campaigns = db.query(Campaign).filter(Campaign.provider == provider).all()
    cids = [c.campaign_id for c in campaigns]
    rows = db.query(CampaignState).filter(CampaignState.campaign_id.in_(cids)).all() if cids else []
    revenue = sum(r.revenue or 0 for r in rows)
    roi_vals = [r.roi for r in rows if r.roi is not None]
    return {
        "id": provider,
        "campaigns": len(campaigns),
        "revenue": round(revenue, 2),
        "roi": round(sum(roi_vals) / len(roi_vals), 4) if roi_vals else None,
    }


COMPARISON_TYPES = frozenset({
    "campaign", "state", "zip", "product", "segment", "provider",
    "month", "quarter", "year",
})


def compare_entities(
    db: Session,
    comparison_type: str,
    entity_a: str,
    entity_b: str,
    upload_id: str | None = None,
) -> dict:
    ctype = comparison_type.lower()
    if ctype not in COMPARISON_TYPES:
        return {"error": f"Unsupported comparison type: {comparison_type}"}

    loaders = {
        "campaign": lambda e: _campaign_snapshot(db, e),
        "state": lambda e: _state_snapshot(db, e, upload_id),
        "zip": lambda e: _zip_snapshot(db, e, upload_id),
        "product": lambda e: _product_snapshot(db, e, upload_id),
        "segment": lambda e: _segment_snapshot(db, e),
        "provider": lambda e: _provider_snapshot(db, e),
    }

    if ctype in loaders:
        a = loaders[ctype](entity_a)
        b = loaders[ctype](entity_b)
    else:
        a = {"id": entity_a, "period": entity_a}
        b = {"id": entity_b, "period": entity_b}

    delta_revenue = None
    if "expected_revenue" in a and "expected_revenue" in b:
        delta_revenue = round((b.get("expected_revenue") or 0) - (a.get("expected_revenue") or 0), 2)
    elif "revenue" in a and "revenue" in b:
        delta_revenue = round((b.get("revenue") or 0) - (a.get("revenue") or 0), 2)

    return {
        "comparison_type": ctype,
        "entity_a": a,
        "entity_b": b,
        "delta": {"revenue": delta_revenue},
        "supported_types": sorted(COMPARISON_TYPES),
    }
