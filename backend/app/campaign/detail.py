"""Volume 06 Section 21 — Campaign Dashboard Detail."""

from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.campaign.forecast import FORECAST_VERSION, RULE_VERSION, compute_campaign_forecast, forecast_accuracy
from app.intelligence.forecasting import le_frame_incentive
from app.models.campaign import Campaign, CampaignProduct, CampaignReportUpload, CampaignState
from app.models.customer import Customer, CustomerIntelligence
from app.models.export import ExportJob
from app.models.learning import CampaignLearning, LearningCampaign
from app.models.zip import ZipIntelligence

from app.reference.registry import PRODUCT_FORECAST_PRICES, SUPPORTED_PRODUCTS

PRODUCTS = list(SUPPORTED_PRODUCTS)


def _index_level(value: float | None) -> str:
    if value is None:
        return "Low"
    if value >= 0.75:
        return "High"
    if value >= 0.45:
        return "Medium"
    return "Low"


def _distribution(rows: list[tuple[Customer, CustomerIntelligence]], pick) -> dict[str, int]:
    return dict(Counter(pick(c, i) or "Unknown" for c, i in rows))


def get_campaign_detail(db: Session, campaign_id: str) -> dict:
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
    if not campaign:
        return {"error": "Campaign not found", "campaign_id": campaign_id}

    state_rows = db.query(CampaignState).filter(CampaignState.campaign_id == campaign_id).all()
    product_rows = db.query(CampaignProduct).filter(CampaignProduct.campaign_id == campaign_id).all()
    learning = db.query(CampaignLearning).filter(CampaignLearning.campaign_id == campaign_id).order_by(
        CampaignLearning.created_at.desc()
    ).first()
    insights = db.query(LearningCampaign).filter(LearningCampaign.campaign_id == campaign_id).all()

    campaign_states = {r.state for r in state_rows if r.state}
    audience_q = db.query(Customer, CustomerIntelligence).join(
        CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id
    )
    if campaign_states:
        audience_q = audience_q.filter(Customer.state.in_(campaign_states))
    audience_rows = audience_q.all()
    if not audience_rows:
        audience_rows = db.query(Customer, CustomerIntelligence).join(
            CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id
        ).limit(500).all()

    target_customers = sum(r.sent for r in state_rows) or len(audience_rows)
    ceragem_dist = _distribution(audience_rows, lambda c, i: i.ceragem_segment)
    prizm_dist = _distribution(audience_rows, lambda c, i: i.prizm_proxy_segment)
    product_dist = _distribution(audience_rows, lambda c, i: i.recommended_product)
    message_dist = _distribution(audience_rows, lambda c, i: i.message_direction)
    pp_dist = _distribution(audience_rows, lambda c, i: _index_level(i.purchase_power_index))
    pain_dist = _distribution(audience_rows, lambda c, i: _index_level(i.pain_index))
    lifestyle_dist = _distribution(audience_rows, lambda c, i: _index_level(i.lifestyle_index))

    total_cost = sum(r.cost or 0 for r in state_rows)
    forecast = compute_campaign_forecast(
        target_customers=target_customers,
        ceragem_distribution=ceragem_dist,
        product_distribution=product_dist,
        campaign_type=campaign.campaign_type or "Email",
        campaign_cost=total_cost or None,
    )

    sent = sum(r.sent for r in state_rows)
    delivered = int(sent * 0.98) if sent else 0
    opened = sum(r.open for r in state_rows)
    clicked = sum(r.click for r in state_rows)
    unique_click = sum(r.unique_click for r in state_rows) or clicked
    actual_revenue = sum(r.revenue or 0 for r in state_rows)
    actual_orders = sum(r.conversion or 0 for r in state_rows) or round(clicked * 0.02, 2)
    actual_conversion = round(actual_orders / max(sent, 1), 6)
    roi_vals = [r.roi for r in state_rows if r.roi is not None]
    campaign_roi = round(sum(roi_vals) / len(roi_vals), 4) if roi_vals else (
        round((actual_revenue - total_cost) / total_cost, 4) if total_cost else None
    )
    accuracy = forecast_accuracy(actual_revenue, forecast["expected_revenue"])

    forecast_vs_actual = [
        {"metric": "Customers", "expected": target_customers, "actual": sent},
        {"metric": "Orders", "expected": forecast["expected_orders"], "actual": actual_orders},
        {"metric": "Revenue", "expected": forecast["expected_revenue"], "actual": round(actual_revenue, 2)},
        {"metric": "Conversion", "expected": round(forecast["expected_conversion"] * 100, 2), "actual": round(actual_conversion * 100, 2)},
        {"metric": "Forecast Accuracy", "expected": 100.0, "actual": round((accuracy or 0) * 100, 2)},
    ]

    zip_refs = {z.zip: z for z in db.query(ZipIntelligence).all()}
    zip_agg: dict[str, dict] = defaultdict(lambda: {
        "zip": "", "city": "", "customers": 0, "purchase_power": "Low",
        "recommended_product": None, "expected_revenue": 0.0, "actual_revenue": 0.0, "campaign_priority": "Low",
    })
    for customer, intel in audience_rows:
        if campaign_states and customer.state not in campaign_states:
            continue
        z = customer.zip or "Unknown"
        ref = zip_refs.get(z)
        agg = zip_agg[z]
        agg["zip"] = z
        agg["city"] = ref.city if ref else (customer.city or "—")
        agg["customers"] += 1
        agg["expected_revenue"] += intel.expected_revenue or 0
        if _index_level(intel.purchase_power_index) == "High":
            agg["purchase_power"] = "High"
        if _index_level(intel.campaign_priority) == "High":
            agg["campaign_priority"] = "High"
        agg["recommended_product"] = intel.recommended_product

    state_perf = []
    for row in state_rows:
        state_customers = sum(1 for c, _ in audience_rows if c.state == row.state)
        state_perf.append({
            "state": row.state or "National",
            "target_customers": state_customers or row.sent,
            "sent": row.sent,
            "ctr": row.ctr,
            "conversion": row.conversion,
            "revenue": round(row.revenue or 0, 2),
            "forecast_accuracy": forecast_accuracy(row.revenue or 0, (row.sent or 0) * (forecast["expected_revenue"] / max(target_customers, 1))),
            "campaign_priority": "High" if row.ctr and row.ctr >= 0.03 else "Medium" if row.ctr and row.ctr >= 0.015 else "Low",
        })

    product_cards = []
    actual_by_product = {p.product: p for p in product_rows if p.product}
    for product in PRODUCTS:
        dist_count = product_dist.get(product, 0)
        expected_orders_p = dist_count * forecast["expected_conversion"]
        expected_rev_p = expected_orders_p * PRODUCT_FORECAST_PRICES.get(product, PRODUCT_FORECAST_PRICES["Master S4"])
        actual_p = actual_by_product.get(product)
        product_cards.append({
            "product": product,
            "target_customers": dist_count,
            "expected_orders": round(expected_orders_p, 2),
            "actual_orders": round((actual_p.conversion or 0) if actual_p else clicked * 0.02 * (dist_count / max(target_customers, 1)), 2),
            "expected_revenue": round(expected_rev_p, 2),
            "actual_revenue": round(actual_p.revenue or 0, 2) if actual_p else 0,
            "conversion": round((actual_p.conversion or 0) / max(actual_p.click, 1), 4) if actual_p and actual_p.click else None,
        })

    report = db.query(CampaignReportUpload).filter(CampaignReportUpload.campaign_id == campaign_id).order_by(
        CampaignReportUpload.created_at.desc()
    ).first()
    export = db.query(ExportJob).filter(ExportJob.campaign == campaign.campaign_name).order_by(
        ExportJob.created_at.desc()
    ).first()

    timeline = [
        {"event": "Campaign Created", "timestamp": campaign.created_at.isoformat() if campaign.created_at else None, "status": "completed"},
        {"event": "Audience Generated", "timestamp": campaign.created_at.isoformat() if campaign.created_at else None, "status": "completed"},
        {"event": "Forecast Completed", "timestamp": campaign.created_at.isoformat() if campaign.created_at else None, "status": "completed"},
        {"event": "Approved", "timestamp": campaign.start_date.isoformat() if campaign.start_date else None, "status": "completed" if campaign.start_date else "pending"},
        {"event": "Exported", "timestamp": export.created_at.isoformat() if export else None, "status": "completed" if export else "pending"},
        {"event": "Executed", "timestamp": campaign.start_date.isoformat() if campaign.start_date else None, "status": "completed" if sent else "pending"},
        {"event": "Report Imported", "timestamp": report.created_at.isoformat() if report else None, "status": "completed" if report else "pending"},
        {"event": "Learning Completed", "timestamp": learning.created_at.isoformat() if learning else None, "status": "completed" if learning else "pending"},
    ]

    top_insight = max(insights, key=lambda x: x.score or 0, default=None) if insights else None
    top_segment = max(ceragem_dist, key=ceragem_dist.get) if ceragem_dist else None
    top_product = max(product_dist, key=product_dist.get) if product_dist else None
    top_state_row = max(state_rows, key=lambda r: r.revenue or 0, default=None) if state_rows else None
    top_zip = max(zip_agg.values(), key=lambda z: z["expected_revenue"], default=None) if zip_agg else None
    top_message = max(message_dist, key=message_dist.get) if message_dist else None

    return {
        "header": {
            "campaign_name": campaign.campaign_name,
            "campaign_id": campaign.campaign_id,
            "campaign_type": campaign.campaign_type or "Email",
            "campaign_owner": campaign.owner or "CIOS Admin",
            "campaign_status": campaign.status or "draft",
            "provider": campaign.provider or "mass_email",
            "campaign_period": {
                "start": campaign.start_date.isoformat() if campaign.start_date else None,
                "end": campaign.end_date.isoformat() if campaign.end_date else None,
            },
            "budget": campaign.budget,
            "forecast_version": campaign.forecast_version or FORECAST_VERSION,
            "rule_version": RULE_VERSION,
        },
        "kpis": {
            "target_customers": target_customers,
            "sent": sent,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "unique_click": unique_click,
            "expected_orders": forecast["expected_orders"],
            "actual_orders": round(actual_orders, 2),
            "expected_revenue": forecast["expected_revenue"],
            "actual_revenue": round(actual_revenue, 2),
            "forecast_accuracy": accuracy,
            "campaign_roi": campaign_roi,
            "le_frame_incentive": le_frame_incentive(actual_revenue or forecast["expected_revenue"]),
        },
        "forecast": forecast,
        "forecast_vs_actual": forecast_vs_actual,
        "audience_distribution": {
            "ceragem": ceragem_dist,
            "prizm": prizm_dist,
            "purchase_power": pp_dist,
            "pain_index": pain_dist,
            "lifestyle": lifestyle_dist,
            "message_direction": message_dist,
        },
        "product_distribution": product_cards,
        "state_performance": state_perf,
        "zip_opportunity": sorted(
            [{**v, "expected_revenue": round(v["expected_revenue"], 2), "actual_revenue": round(v["actual_revenue"], 2)} for v in zip_agg.values()],
            key=lambda x: -x["expected_revenue"],
        )[:50],
        "timeline": timeline,
        "learning_summary": {
            "top_performing_segment": top_segment,
            "top_product": top_product,
            "highest_conversion_state": top_state_row.state if top_state_row else None,
            "highest_revenue_zip": top_zip["zip"] if top_zip else None,
            "best_message_direction": top_message,
            "recommendation_for_next_campaign": top_insight.recommendation if top_insight else (
                learning and f"Repeat strategy with forecast accuracy {round((learning.forecast_accuracy or 0) * 100, 1)}%"
            ) or "Run audience generation and forecast before next campaign.",
            "learning_record": {
                "learning_id": str(learning.learning_id) if learning else None,
                "learning_score": learning.learning_score if learning else None,
                "forecast_accuracy": learning.forecast_accuracy if learning else accuracy,
            } if learning or accuracy else None,
        },
    }
