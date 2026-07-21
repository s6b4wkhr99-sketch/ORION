"""Dashboard analytics — reads Chapter 6 database tables."""

import json
import uuid
from collections import Counter, defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session, defer, joinedload

from app.intelligence.recommendation_rationale import rationale_from_framework_summary
from app.intelligence.forecasting import le_frame_incentive
from app.models.campaign import Campaign, CampaignProduct, CampaignReportUpload, CampaignState
from app.models.customer import Customer, CustomerDatalogix, CustomerIntelligence
from app.models.learning import LearningCampaign
from app.models.raw import RawUpload
from app.utils.timezone import iso_app


def _parse_upload_id(upload_id: str | None):
    return uuid.UUID(upload_id) if upload_id else None


def _targetable_filter():
    return Customer.email.isnot(None)


def _aggregate_campaign_performance(db: Session) -> dict:
    rows = db.query(CampaignState).all()
    if not rows:
        return {"total_sent": 0, "total_revenue": 0, "avg_roi": None, "campaign_count": 0}

    total_sent = sum(r.sent for r in rows)
    total_open = sum(r.open for r in rows)
    total_click = sum(r.click for r in rows)
    total_revenue = sum(r.revenue or 0 for r in rows)
    total_cost = sum(r.cost or 0 for r in rows)
    roi_values = [r.roi for r in rows if r.roi is not None]
    campaign_ids = {r.campaign_id for r in rows}
    avg_roi = round(sum(roi_values) / len(roi_values), 4) if roi_values else (
        round((total_revenue - total_cost) / total_cost, 4) if total_cost else None
    )

    return {
        "total_sent": total_sent,
        "total_open": total_open,
        "total_click": total_click,
        "total_revenue": round(total_revenue, 2),
        "total_cost": round(total_cost, 2),
        "avg_roi": avg_roi,
        "open_rate": round(total_open / total_sent, 4) if total_sent else None,
        "ctr": round(total_click / total_sent, 4) if total_sent else None,
        "campaign_count": len(campaign_ids),
    }


def get_executive_summary(db: Session, upload_id: str | None = None) -> dict:
    from app.campaign.executive_dashboard import build_executive_dashboard

    return build_executive_dashboard(db, upload_id)


def get_customer_distribution(db: Session, upload_id: str | None = None) -> dict:
    uid = _parse_upload_id(upload_id)
    state_q = db.query(Customer.state, func.count(Customer.customer_id))
    zip_q = db.query(Customer.zip, func.count(Customer.customer_id))
    if uid:
        state_q = state_q.filter(Customer.upload_id == uid)
        zip_q = zip_q.filter(Customer.upload_id == uid)

    by_state = state_q.group_by(Customer.state).all()
    by_zip = zip_q.group_by(Customer.zip).order_by(func.count(Customer.customer_id).desc()).limit(50).all()

    seg_q = db.query(CustomerIntelligence).join(Customer)
    if uid:
        seg_q = seg_q.filter(Customer.upload_id == uid)
    segments = seg_q.all()

    dlx_q = db.query(CustomerDatalogix).join(Customer)
    if uid:
        dlx_q = dlx_q.filter(Customer.upload_id == uid)
    dlx_rows = dlx_q.all()

    return {
        "by_state": [{"state": s or "Unknown", "count": c} for s, c in by_state],
        "by_zip": [{"zip": z or "Unknown", "count": c} for z, c in by_zip],
        "prizm_distribution": dict(Counter(s.prizm_proxy_segment for s in segments)),
        "ceragem_distribution": dict(Counter(s.ceragem_segment for s in segments)),
        "datalogix_online_access": dict(Counter(r.online_access for r in dlx_rows)),
        "datalogix_retail_card": dict(Counter(r.retail_card for r in dlx_rows)),
        "average_indices": {
            "email_responsiveness_index": round(sum(s.email_response_index or 0 for s in segments) / max(len(segments), 1), 4),
            "purchase_power_index": round(sum(s.purchase_power_index or 0 for s in segments) / max(len(segments), 1), 4),
            "lifestyle_index": round(sum(s.lifestyle_index or 0 for s in segments) / max(len(segments), 1), 4),
            "pain_index": round(sum(s.pain_index or 0 for s in segments) / max(len(segments), 1), 4),
            "brand_familiarity_index": round(sum(s.brand_familiarity_index or 0 for s in segments) / max(len(segments), 1), 4),
        },
    }


def _rationale_fields(intel: CustomerIntelligence) -> dict:
    if not getattr(intel, "framework_summary_json", None):
        return {}
    try:
        summary = json.loads(intel.framework_summary_json)
        rationale = rationale_from_framework_summary(summary)
        if not rationale:
            return {}
        return {
            "sleep_segment": rationale.get("sleep_segment"),
            "sleep_segment_label": rationale.get("sleep_segment_label"),
            "recommendation_rationale_summary": rationale.get("summary"),
        }
    except json.JSONDecodeError:
        return {}


def get_customer_table(
    db: Session,
    upload_id: str | None = None,
    state: str | None = None,
    segment: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    uid = _parse_upload_id(upload_id)
    q = db.query(Customer, CustomerIntelligence).join(
        CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id
    ).options(
        defer(CustomerIntelligence.trace_json),
        defer(CustomerIntelligence.framework_json),
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    if state:
        q = q.filter(Customer.state == state)
    if segment:
        q = q.filter(CustomerIntelligence.prizm_proxy_segment == segment)

    total = q.count()
    rows = q.order_by(CustomerIntelligence.campaign_priority.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "items": [{
            "id": str(c.customer_id),
            "email": c.email,
            "name": " ".join(p for p in [c.first_name, c.last_name] if p) or None,
            "state": c.state,
            "zip": c.zip,
            "prizm_proxy_segment": s.prizm_proxy_segment,
            "ceragem_segment": s.ceragem_segment,
            "message_direction": s.message_direction,
            "recommended_product": s.recommended_product,
            "purchase_power_index": s.purchase_power_index,
            "pain_index": s.pain_index,
            "lifestyle_index": s.lifestyle_index,
            "email_response_index": s.email_response_index,
            "brand_familiarity_index": s.brand_familiarity_index,
            "expected_conversion_rate": s.expected_conversion,
            "expected_revenue": s.expected_revenue,
            "campaign_priority": s.campaign_priority,
            "promo_code": s.promo_code,
            "recommended_promotion": s.recommended_promotion,
            "price_resistance_score": s.price_resistance_score,
            "commercial_version": s.commercial_version,
            **_rationale_fields(s),
        } for c, s in rows],
    }


def get_retail_intelligence(
    db: Session,
    upload_id: str | None = None,
    state: str | None = None,
    segment: str | None = None,
    product: str | None = None,
) -> dict:
    uid = _parse_upload_id(upload_id)
    q = db.query(Customer, CustomerIntelligence).join(
        CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id
    )
    if uid:
        q = q.filter(Customer.upload_id == uid)
    if state:
        q = q.filter(Customer.state == state)
    if segment:
        q = q.filter(CustomerIntelligence.prizm_proxy_segment == segment)
    if product:
        q = q.filter(CustomerIntelligence.recommended_product == product)

    rows = q.all()
    state_stats: dict[str, dict] = defaultdict(lambda: {"count": 0, "revenue": 0.0})
    zip_stats: dict[str, dict] = defaultdict(lambda: {"count": 0, "revenue": 0.0, "state": ""})
    table_rows = []

    for customer, seg in rows:
        st = customer.state or "Unknown"
        zp = customer.zip or "Unknown"
        rev = seg.expected_revenue or 0
        state_stats[st]["count"] += 1
        state_stats[st]["revenue"] += rev
        zip_stats[zp]["count"] += 1
        zip_stats[zp]["revenue"] += rev
        zip_stats[zp]["state"] = st
        table_rows.append({
            "state": st, "zip": zp,
            "prizm_proxy_segment": seg.prizm_proxy_segment,
            "ceragem_segment": seg.ceragem_segment,
            "target_count": 1,
            "recommended_product": seg.recommended_product,
            "message_direction": seg.message_direction,
            "expected_conversion_rate": seg.expected_conversion,
            "expected_orders": seg.expected_conversion,
            "expected_revenue": seg.expected_revenue,
            "campaign_priority": seg.campaign_priority,
        })

    table_rows.sort(key=lambda r: r.get("campaign_priority") or 0, reverse=True)

    return {
        "state_performance": [
            {"state": k, "count": v["count"], "revenue": round(v["revenue"], 2)}
            for k, v in sorted(state_stats.items(), key=lambda x: -x[1]["revenue"])
        ],
        "zip_heatmap": [
            {"zip": k, "state": v["state"], "count": v["count"], "revenue": round(v["revenue"], 2)}
            for k, v in sorted(zip_stats.items(), key=lambda x: -x[1]["revenue"])[:100]
        ],
        "segment_revenue_matrix": [],
        "opportunity_table": table_rows[:200],
    }


def get_campaign_dashboard(db: Session, campaign_id: str | None = None) -> dict:
    state_q = db.query(CampaignState)
    product_q = db.query(CampaignProduct)
    if campaign_id:
        state_q = state_q.filter(CampaignState.campaign_id == campaign_id)
        product_q = product_q.filter(CampaignProduct.campaign_id == campaign_id)

    state_rows = state_q.all()
    product_rows = product_q.all()
    insights = db.query(LearningCampaign)
    if campaign_id:
        insights = insights.filter(LearningCampaign.campaign_id == campaign_id)
    insights = insights.order_by(LearningCampaign.score.desc()).all()

    by_state: dict[str, dict] = defaultdict(lambda: {"sent": 0, "open": 0, "click": 0, "revenue": 0.0, "cost": 0.0})
    for row in state_rows:
        st = row.state or "National"
        by_state[st]["sent"] += row.sent
        by_state[st]["open"] += row.open
        by_state[st]["click"] += row.click
        by_state[st]["revenue"] += row.revenue or 0
        by_state[st]["cost"] += row.cost or 0

    overview = _aggregate_campaign_performance(db)
    if campaign_id and state_rows:
        total_sent = sum(r.sent for r in state_rows)
        total_open = sum(r.open for r in state_rows)
        total_click = sum(r.click for r in state_rows)
        total_revenue = sum(r.revenue or 0 for r in state_rows)
        total_cost = sum(r.cost or 0 for r in state_rows)
        roi_values = [r.roi for r in state_rows if r.roi is not None]
        overview = {
            "total_sent": total_sent,
            "total_open": total_open,
            "total_click": total_click,
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "avg_roi": round(sum(roi_values) / len(roi_values), 4) if roi_values else None,
            "open_rate": round(total_open / total_sent, 4) if total_sent else None,
            "ctr": round(total_click / total_sent, 4) if total_sent else None,
            "campaign_count": 1,
        }

    campaigns = db.query(Campaign).all()
    primary = campaigns[0] if campaigns else None
    total_sent = overview.get("total_sent", 0)
    total_open = overview.get("total_open", 0)
    total_click = overview.get("total_click", 0)
    delivered = int(total_sent * 0.98) if total_sent else 0
    unique_click = sum(r.unique_click for r in state_rows) if state_rows else total_click
    le_frame = round(overview.get("total_revenue", 0) * 0.15, 2)

    funnel = [
        {"stage": "Sent", "value": total_sent},
        {"stage": "Delivered", "value": delivered},
        {"stage": "Opened", "value": total_open},
        {"stage": "Clicked", "value": total_click},
        {"stage": "Landing", "value": int(total_click * 0.85)},
        {"stage": "Product Detail", "value": int(total_click * 0.55)},
        {"stage": "Purchase", "value": int(total_click * 0.08)},
    ]

    top_insight = insights[0] if insights else None

    return {
        "campaign_overview": {
            "campaign_name": primary.campaign_name if primary else None,
            "campaign_type": primary.campaign_type if primary else None,
            "provider": primary.provider if primary else None,
            "start_date": primary.start_date.isoformat() if primary and primary.start_date else None,
            "end_date": primary.end_date.isoformat() if primary and primary.end_date else None,
            "status": primary.status if primary else None,
            "budget": primary.budget if primary else None,
            "owner": "CIOS Admin",
        },
        "overview": {
            **overview,
            "total_delivered": delivered,
            "unique_click": unique_click,
            "ctor": round(total_click / total_open, 4) if total_open else None,
            "expected_orders": round(total_click * 0.02, 2),
            "le_frame_incentive": le_frame,
        },
        "funnel": funnel,
        "ai_summary": {
            "campaign_score": round((overview.get("avg_roi") or 0.5) * 100),
            "business_summary": top_insight.insight_summary if top_insight else "Import campaign reports to generate AI performance summary.",
            "key_opportunity": top_insight.recommendation if top_insight else "Target high-intent segments with premium wellness messaging.",
            "key_risk": "Monitor states with below-average CTR and adjust message direction.",
            "recommended_next_action": "Create follow-up campaign for engaged non-converters.",
        },
        "state_performance": [
            {
                "state": st,
                **stats,
                "delivered": int(stats["sent"] * 0.98),
                "revenue": round(stats["revenue"], 2),
                "roi": round((stats["revenue"] - stats["cost"]) / stats["cost"], 4) if stats["cost"] else None,
                "open_rate": round(stats["open"] / stats["sent"], 4) if stats["sent"] else None,
                "ctr": round(stats["click"] / stats["sent"], 4) if stats["sent"] else None,
            }
            for st, stats in sorted(by_state.items(), key=lambda x: -x[1]["revenue"])
        ],
        "click_categories": [
            {"campaign_id": p.campaign_id, "state": None, "category": p.category,
             "product": p.product, "click_count": p.click, "click_rate": p.click_rate}
            for p in product_rows
        ],
        "learning_insights": [
            {"id": str(i.id), "campaign_id": i.campaign_id, "campaign_name": i.campaign_id,
             "state": i.state, "product": i.product, "insight_summary": i.insight_summary,
             "recommendation": i.recommendation, "confidence_score": i.score, "roi": i.roi, "ctr": None}
            for i in insights
        ],
        "campaigns": [{"campaign_id": c.campaign_id, "campaign_name": c.campaign_name} for c in campaigns],
    }


def list_uploads(db: Session) -> list[dict]:
    uploads = db.query(RawUpload).order_by(RawUpload.uploaded_date.desc()).all()
    return [{
        "id": str(u.upload_id),
        "file_name": u.filename,
        "total_rows": json.loads(u.summary_json).get("total_rows", 0) if u.summary_json else 0,
        "valid_emails": json.loads(u.summary_json).get("valid_emails", 0) if u.summary_json else 0,
        "status": u.status,
        "created_at": iso_app(u.uploaded_date) if u.uploaded_date else None,
        "summary": json.loads(u.summary_json) if u.summary_json else None,
    } for u in uploads]


def list_campaign_reports(db: Session) -> list[dict]:
    reports = db.query(CampaignReportUpload).order_by(CampaignReportUpload.created_at.desc()).all()
    return [{
        "id": str(r.id),
        "file_name": r.filename,
        "campaign_id": r.campaign_id,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "summary": json.loads(r.summary_json) if r.summary_json else None,
    } for r in reports]


def get_learning_insights(db: Session, limit: int = 20) -> list[dict]:
    rows = db.query(LearningCampaign).order_by(LearningCampaign.score.desc()).limit(limit).all()
    return [{
        "id": str(r.id),
        "campaign_id": r.campaign_id,
        "campaign_name": r.campaign_id,
        "state": r.state,
        "segment": r.segment,
        "product": r.product,
        "insight_summary": r.insight_summary,
        "recommendation": r.recommendation,
        "confidence_score": r.score,
        "roi": r.roi,
        "revenue": r.revenue,
    } for r in rows]
