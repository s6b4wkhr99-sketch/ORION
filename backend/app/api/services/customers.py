"""Volume 07 Section 4–5 — Customer API services."""

import json
import uuid

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.intelligence.recommendation_rationale import rationale_from_framework_summary, rationale_from_intelligence_row
from app.models.customer import Customer, CustomerIntelligence


def _index_level(value: float | None) -> str:
    if value is None:
        return "Low"
    if value >= 0.75:
        return "High"
    if value >= 0.45:
        return "Medium"
    return "Low"


def _index_level_filter(column, level: str):
    if level == "High":
        return column >= 0.75
    if level == "Medium":
        return (column >= 0.45) & (column < 0.75)
    return or_(column.is_(None), column < 0.45)


def _load_rationale(intel: CustomerIntelligence, customer: Customer) -> dict | None:
    if getattr(intel, "framework_summary_json", None):
        try:
            summary = json.loads(intel.framework_summary_json)
            stored = rationale_from_framework_summary(summary)
            if stored:
                return stored
        except json.JSONDecodeError:
            pass
    return rationale_from_intelligence_row(intel, customer)


def _customer_row(c: Customer, i: CustomerIntelligence) -> dict:
    rationale = _load_rationale(i, c)
    return {
        "id": str(c.customer_id),
        "email": c.email,
        "name": " ".join(p for p in [c.first_name, c.last_name] if p) or None,
        "state": c.state,
        "zip": c.zip,
        "city": c.city,
        "prizmProxySegment": i.prizm_proxy_segment,
        "ceragemSegment": i.ceragem_segment,
        "messageDirection": i.message_direction,
        "recommendedProduct": i.recommended_product,
        "purchasePower": _index_level(i.purchase_power_index),
        "painIndex": _index_level(i.pain_index),
        "lifestyle": _index_level(i.lifestyle_index),
        "digitalEngagement": _index_level(i.email_response_index),
        "brandFamiliarity": _index_level(i.brand_familiarity_index),
        "campaignPriority": _index_level(i.campaign_priority),
        "expectedConversion": i.expected_conversion,
        "expectedRevenue": i.expected_revenue,
        "emailResponseIndex": i.email_response_index,
        "brandFamiliarityIndex": i.brand_familiarity_index,
        "sleepSegment": (rationale or {}).get("sleep_segment"),
        "sleepSegmentLabel": (rationale or {}).get("sleep_segment_label"),
        "recommendationRationaleSummary": (rationale or {}).get("summary"),
    }


def _apply_customer_filters(
    q,
    *,
    upload_id: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    segment: str | None = None,
    purchase_power: str | None = None,
    pain_index: str | None = None,
    product: str | None = None,
    campaign_priority: str | None = None,
):
    if upload_id:
        q = q.filter(Customer.upload_id == uuid.UUID(upload_id))
    if state:
        q = q.filter(Customer.state == state)
    if zip_code:
        q = q.filter(Customer.zip == zip_code)
    if segment:
        q = q.filter(CustomerIntelligence.prizm_proxy_segment == segment)
    if product:
        q = q.filter(CustomerIntelligence.recommended_product == product)
    if purchase_power:
        q = q.filter(_index_level_filter(CustomerIntelligence.purchase_power_index, purchase_power))
    if pain_index:
        q = q.filter(_index_level_filter(CustomerIntelligence.pain_index, pain_index))
    if campaign_priority:
        q = q.filter(_index_level_filter(CustomerIntelligence.campaign_priority, campaign_priority))
    return q


def list_customers(
    db: Session,
    *,
    page: int = 1,
    limit: int = 100,
    upload_id: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    segment: str | None = None,
    purchase_power: str | None = None,
    pain_index: str | None = None,
    product: str | None = None,
    campaign_priority: str | None = None,
) -> dict:
    limit = min(max(limit, 1), 500)
    page = max(page, 1)
    offset = (page - 1) * limit

    count_q = _apply_customer_filters(
        db.query(func.count(Customer.customer_id))
        .select_from(Customer)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id),
        upload_id=upload_id,
        state=state,
        zip_code=zip_code,
        segment=segment,
        purchase_power=purchase_power,
        pain_index=pain_index,
        product=product,
        campaign_priority=campaign_priority,
    )
    total = int(count_q.scalar() or 0)

    page_q = _apply_customer_filters(
        db.query(Customer, CustomerIntelligence).join(
            CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id
        ),
        upload_id=upload_id,
        state=state,
        zip_code=zip_code,
        segment=segment,
        purchase_power=purchase_power,
        pain_index=pain_index,
        product=product,
        campaign_priority=campaign_priority,
    )
    page_rows = (
        page_q.order_by(Customer.customer_id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "total": int(total),
        "page": page,
        "limit": limit,
        "rows": [_customer_row(c, i) for c, i in page_rows],
    }


def get_customer_detail(db: Session, customer_id: str) -> dict | None:
    try:
        cid = uuid.UUID(customer_id)
    except ValueError:
        return None
    row = (
        db.query(Customer, CustomerIntelligence)
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(Customer.customer_id == cid)
        .first()
    )
    if not row:
        return None
    c, i = row
    rationale = _load_rationale(i, c)
    data = _customer_row(c, i)
    data.update({
        "phone": c.phone,
        "address": c.address,
        "country": c.country,
        "permission": c.permission,
        "purchasePowerIndex": i.purchase_power_index,
        "painIndexValue": i.pain_index,
        "lifestyleIndex": i.lifestyle_index,
        "campaignPriorityValue": i.campaign_priority,
        "recommendationRationale": rationale,
    })
    return data


def get_customer_intelligence(db: Session, customer_id: str) -> dict | None:
    detail = get_customer_detail(db, customer_id)
    if not detail:
        return None
    return {
        "customerId": customer_id,
        "prizmProxy": detail["prizmProxySegment"],
        "ceragemSegment": detail["ceragemSegment"],
        "purchasePower": detail["purchasePower"],
        "painIndex": detail["painIndex"],
        "lifestyle": detail["lifestyle"],
        "digitalEngagement": detail.get("digitalEngagement"),
        "brandFamiliarity": detail.get("brandFamiliarity"),
        "emailResponseIndex": detail.get("emailResponseIndex"),
        "brandFamiliarityIndex": detail.get("brandFamiliarityIndex"),
        "sleepSegment": detail.get("sleepSegment"),
        "sleepSegmentLabel": detail.get("sleepSegmentLabel"),
        "recommendation": {
            "product": detail["recommendedProduct"],
            "messageDirection": detail["messageDirection"],
            "campaignPriority": detail["campaignPriority"],
            "rationale": detail.get("recommendationRationale"),
            "rationaleSummary": detail.get("recommendationRationaleSummary"),
        },
        "revenue": {
            "expectedConversion": detail["expectedConversion"],
            "expectedRevenue": detail["expectedRevenue"],
        },
    }


def get_customer_recommendation(db: Session, customer_id: str) -> dict | None:
    intel = get_customer_intelligence(db, customer_id)
    if not intel:
        return None
    return {
        "customerId": customer_id,
        "recommendedProduct": intel["recommendation"]["product"],
        "messageDirection": intel["recommendation"]["messageDirection"],
        "campaignPriority": intel["recommendation"]["campaignPriority"],
        "expectedRevenue": intel["revenue"]["expectedRevenue"],
        "expectedConversion": intel["revenue"]["expectedConversion"],
        "recommendationRationale": intel["recommendation"].get("rationale"),
        "rationaleSummary": intel["recommendation"].get("rationaleSummary"),
    }
