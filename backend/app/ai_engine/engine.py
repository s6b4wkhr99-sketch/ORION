"""Volume 18 — AI Intelligence & Recommendation Engine orchestrator."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.ai_engine.confidence import adjust_confidence, base_confidence, confidence_category
from app.ai_engine.constants import (
    CAMPAIGN_TYPES,
    ENGINE_VERSION,
    LEARNING_VERSION,
    MESSAGE_DIRECTION_MAP,
    MESSAGE_TYPES,
    PRODUCT_ALTERNATIVES,
    PRODUCTS,
    RULE_VERSION,
    STRATEGY_TO_CAMPAIGN,
)
from app.ai_engine.learning import (
    learning_adjustment_for_message,
    learning_adjustment_for_product,
    learning_adjustment_for_state,
)
from app.reference.registry import PRODUCT_FORECAST_PRICES, PRODUCT_PRICES
from app.intelligence.forecasting import forecast_customer
from app.intelligence.recommendation_rationale import rationale_from_framework_summary, rationale_from_intelligence_row
from app.intelligence.recommendation_rules import build_recommendation_inputs, evaluate_recommendation
from app.intelligence.types import IntelligenceContext
from app.models.customer import Customer, CustomerDatalogix, CustomerIntelligence
from app.models.v16_schema import Recommendation
from app.models.zip import ZipIntelligence
from app.rules.library import DASHBOARD_RULE_MAP


def _index_level(value: float | None) -> str:
    if value is None:
        return "Low"
    if value >= 0.75:
        return "High"
    if value >= 0.45:
        return "Medium"
    return "Low"


def analyze_customer_profile(db: Session, customer: Customer, intel: CustomerIntelligence) -> dict:
    dlx = db.query(CustomerDatalogix).filter(CustomerDatalogix.customer_id == customer.customer_id).first()
    zip_ref = db.query(ZipIntelligence).filter(ZipIntelligence.zip == customer.zip).first() if customer.zip else None

    zip_intel: dict[str, Any] = {
        "premium_zip_indicator": bool(zip_ref and getattr(zip_ref, "top50_rank", False)),
        "median_income": zip_ref.median_income if zip_ref else None,
    }
    rationale = None
    if getattr(intel, "framework_summary_json", None):
        try:
            summary = json.loads(intel.framework_summary_json)
            rationale = rationale_from_framework_summary(summary)
            sleep_cat = (summary.get("categories") or {}).get("sleep_affinity") or {}
            if sleep_cat.get("sleep_segment"):
                zip_intel["sleep_segment"] = sleep_cat["sleep_segment"]
            if sleep_cat.get("sleep_geo_boost") is not None:
                zip_intel["sleep_geo_boost"] = sleep_cat["sleep_geo_boost"]
        except json.JSONDecodeError:
            pass
    if not rationale:
        rationale = rationale_from_intelligence_row(intel, customer)

    ctx = IntelligenceContext(
        customer={"state": customer.state, "zip": customer.zip, "city": customer.city},
        prizm_proxy_segment=intel.prizm_proxy_segment,
        ceragem_segment=intel.ceragem_segment,
        message_direction=intel.message_direction,
        purchase_power_index=intel.purchase_power_index or 0,
        purchase_power_category=_index_level(intel.purchase_power_index),
        pain_index=intel.pain_index or 0,
        pain_index_category=_index_level(intel.pain_index),
        lifestyle_index=intel.lifestyle_index or 0,
        lifestyle_category=_index_level(intel.lifestyle_index),
        email_response_index=intel.email_response_index or 0,
        brand_familiarity_index=intel.brand_familiarity_index or 0,
        recommended_product=intel.recommended_product,
        campaign_strategy=None,
        zip_intelligence=zip_intel,
        recommendation_rationale=rationale or {},
    )

    inputs = build_recommendation_inputs(ctx)
    rule_result = evaluate_recommendation(inputs)

    intelligence_score = round(
        (intel.purchase_power_index or 0) * 30
        + (intel.pain_index or 0) * 20
        + (intel.lifestyle_index or 0) * 20
        + (intel.email_response_index or 0) * 30,
        2,
    )
    base_conf = base_confidence(intel.campaign_priority or 0.5, intel.email_response_index or 0)

    return {
        "customer_intelligence_score": intelligence_score,
        "confidence_score": base_conf,
        "recommendation_context": {
            "ceragem_segment": intel.ceragem_segment,
            "prizm_proxy_segment": intel.prizm_proxy_segment,
            "purchase_power": inputs.purchase_power_category,
            "pain_index": inputs.pain_index_category,
            "lifestyle": inputs.lifestyle_category,
            "state": customer.state,
            "zip": customer.zip,
            "premium_zip": inputs.premium_zip,
            "age_range": dlx.age_range if dlx else None,
            "generation": dlx.generation if dlx else None,
        },
        "rule_result": rule_result,
        "inputs": inputs,
        "recommendation_rationale": rationale,
    }


def _product_recommendation(db: Session, analysis: dict) -> dict:
    primary = analysis["rule_result"]["product"]["recommended_product"]
    alts = PRODUCT_ALTERNATIVES.get(primary, ("Master V6", "Pause M2"))
    adj = learning_adjustment_for_product(db, primary)
    conf = adjust_confidence(analysis["confidence_score"], adj)
    reasons = []
    ctx = analysis["recommendation_context"]
    rationale = analysis.get("recommendation_rationale") or {}
    for factor in rationale.get("factors", []):
        if isinstance(factor, dict):
            reasons.append(f"{factor.get('label')}: {factor.get('level')} ({factor.get('score')}%)")
    if rationale.get("selection_rule"):
        reasons.append(f"선정 기준: {rationale['selection_rule']}")
    for adjustment in rationale.get("adjustments", []):
        if isinstance(adjustment, dict):
            reasons.append(f"{adjustment.get('label')}: {adjustment.get('detail')}")
    if ctx["purchase_power"] == "High":
        reasons.append("High Purchase Power")
    if ctx["pain_index"] == "High":
        reasons.append("High Pain Index")
    if ctx.get("premium_zip"):
        reasons.append("Premium ZIP")
    if "Technology" in (analysis["inputs"].message_direction or ""):
        reasons.append("Technology Preference")
    if adj > 8:
        reasons.append("Previous Campaign Success")
    rules = [DASHBOARD_RULE_MAP.get("recommended_product", "RULE-REC-001")]

    return {
        "primary": primary,
        "secondary": alts[0],
        "backup": alts[1],
        "confidence": conf,
        "confidence_category": confidence_category(conf),
        "reason": reasons or ["Ceragem segment and business rule match"],
        "selection_rule": rationale.get("selection_rule"),
        "factors": rationale.get("factors", []),
        "adjustments": rationale.get("adjustments", []),
        "rationale_summary": rationale.get("summary"),
        "business_rules_used": rules,
        "ranking": [
            {"rank": 1, "product": primary, "confidence": conf},
            {"rank": 2, "product": alts[0], "confidence": adjust_confidence(conf, -8)},
            {"rank": 3, "product": alts[1], "confidence": adjust_confidence(conf, -15)},
        ],
    }


def _message_recommendation(db: Session, analysis: dict) -> dict:
    direction = analysis["inputs"].message_direction or "Product Education Message"
    primary = MESSAGE_DIRECTION_MAP.get(direction, "Technology")
    secondary = "Consultation" if primary != "Consultation" else "Pain Relief"
    adj = learning_adjustment_for_message(db, direction)
    conf = adjust_confidence(analysis["confidence_score"], adj)
    return {
        "primary": primary,
        "secondary": secondary,
        "confidence": conf,
        "confidence_category": confidence_category(conf),
        "reason": [f"Message direction: {direction}", f"Ceragem segment: {analysis['recommendation_context']['ceragem_segment']}"],
        "supported_types": list(MESSAGE_TYPES),
    }


def _campaign_recommendation(db: Session, analysis: dict) -> dict:
    strategy = analysis["rule_result"]["strategy"]["campaign_strategy"]
    campaign_type = STRATEGY_TO_CAMPAIGN.get(strategy, "Education")
    if campaign_type not in CAMPAIGN_TYPES:
        campaign_type = "Consultation"
    conf = adjust_confidence(analysis["confidence_score"], learning_adjustment_for_product(db, analysis["rule_result"]["product"]["recommended_product"]) / 2)
    return {
        "recommended_campaign": campaign_type,
        "campaign_strategy": strategy,
        "expected_conversion": analysis.get("expected_conversion"),
        "expected_revenue": analysis.get("expected_revenue"),
        "confidence": conf,
        "confidence_category": confidence_category(conf),
        "reason": [f"Business rule strategy: {strategy}"],
    }


def _geographic_recommendation(db: Session, customer: Customer, analysis: dict) -> dict:
    state = customer.state or "National"
    zip_code = customer.zip or "Unknown"
    state_adj = learning_adjustment_for_state(db, state)
    priority = analysis["rule_result"]["priority"]["campaign_priority"]
    rev = analysis.get("expected_revenue") or 0
    return {
        "recommended_state": state,
        "recommended_zip": zip_code,
        "recommended_region": state,
        "campaign_priority": priority,
        "revenue_opportunity": round(rev, 2),
        "conversion_opportunity": analysis.get("expected_conversion"),
        "confidence": adjust_confidence(analysis["confidence_score"], state_adj),
    }


def _revenue_prediction(analysis: dict, product: str) -> dict:
    price = PRODUCT_FORECAST_PRICES.get(product, PRODUCT_FORECAST_PRICES["Master S4"])
    expected = analysis.get("expected_revenue") or round((analysis.get("expected_conversion") or 0) * price, 2)
    low = round(expected * 0.85, 2)
    high = round(expected * 1.15, 2)
    conf = analysis["confidence_score"]
    return {
        "expected_revenue": round(expected, 2),
        "revenue_range": {"low": low, "high": high},
        "confidence": conf,
        "confidence_category": confidence_category(conf),
        "forecast_interval": "conservative",
        "business_rule_id": DASHBOARD_RULE_MAP.get("expected_revenue", "RULE-FOR-002"),
    }


def _conversion_prediction(analysis: dict) -> dict:
    rate = analysis.get("expected_conversion") or 0
    priority = analysis["rule_result"]["priority"]["campaign_priority"]
    conf = analysis["confidence_score"]
    return {
        "expected_conversion": round(rate, 6),
        "confidence": conf,
        "confidence_category": confidence_category(conf),
        "expected_purchase_window": "30-60 days" if priority == "High" else "60-90 days",
        "campaign_priority": priority,
    }


def _ai_scores(analysis: dict, product_rec: dict, campaign_rec: dict) -> dict:
    intel_score = analysis["customer_intelligence_score"]
    rev_score = min(100, round((analysis.get("expected_revenue") or 0) / 100, 2))
    conv_score = min(100, round((analysis.get("expected_conversion") or 0) * 10000, 2))
    return {
        "customer_score": intel_score,
        "revenue_score": rev_score,
        "conversion_score": conv_score,
        "campaign_score": campaign_rec["confidence"],
        "recommendation_score": product_rec["confidence"],
        "priority_score": round((analysis["rule_result"]["priority"]["campaign_priority_score"] or 0.5) * 100, 2),
        "learning_score": round(analysis["confidence_score"], 2),
    }


def _business_priority(scores: dict, priority_label: str) -> str:
    if priority_label == "High" and scores["recommendation_score"] >= 70:
        return "A"
    if priority_label == "High" or scores["recommendation_score"] >= 60:
        return "B"
    if priority_label == "Medium" or scores["recommendation_score"] >= 40:
        return "C"
    return "D"


def _campaign_readiness(scores: dict, priority: str) -> str:
    if scores["recommendation_score"] >= 70 and priority in {"A", "B"}:
        return "Ready"
    if scores["recommendation_score"] >= 50:
        return "Review"
    return "Hold"


def run_ai_recommendation_for_intelligence(
    db: Session,
    customer: Customer,
    intel: CustomerIntelligence,
    *,
    generated_by: str = "ai_engine",
) -> dict[str, Any]:
    """
    Volume 18 workflow: Business Rules → Learning → AI ranking → persist.
    """
    analysis = analyze_customer_profile(db, customer, intel)
    forecast = forecast_customer(
        ceragem_segment=intel.ceragem_segment or "Mid-Low + Wellness",
        recommended_product=analysis["rule_result"]["product"]["recommended_product"],
    )
    analysis["expected_conversion"] = intel.expected_conversion or forecast.get("conversion_rate", 0)
    analysis["expected_revenue"] = intel.expected_revenue or forecast.get("expected_revenue", 0)
    analysis["confidence_score"] = adjust_confidence(
        analysis["confidence_score"],
        learning_adjustment_for_product(db, analysis["rule_result"]["product"]["recommended_product"]),
    )

    product_rec = _product_recommendation(db, analysis)
    message_rec = _message_recommendation(db, analysis)
    campaign_rec = _campaign_recommendation(db, analysis)
    geo_rec = _geographic_recommendation(db, customer, analysis)
    revenue_pred = _revenue_prediction(analysis, product_rec["primary"])
    conversion_pred = _conversion_prediction(analysis)
    scores = _ai_scores(analysis, product_rec, campaign_rec)
    priority_label = analysis["rule_result"]["priority"]["campaign_priority"]
    business_priority = _business_priority(scores, priority_label)
    readiness = _campaign_readiness(scores, business_priority)

    reason_parts = product_rec["reason"] + message_rec["reason"][:1]
    reason_text = "; ".join(reason_parts)
    rules_used = list({
        DASHBOARD_RULE_MAP.get("recommended_product", "RULE-REC-001"),
        DASHBOARD_RULE_MAP.get("prizm_proxy_segment", "RULE-PRZ-001"),
        DASHBOARD_RULE_MAP.get("ceragem_segment", "RULE-SEG-001"),
        "RULE-PUR-001",
        "RULE-PAI-002",
        "RULE-SLP-001",
    })

    payload = {
        "recommendation_id": None,
        "customer_id": str(customer.customer_id),
        "engine_version": ENGINE_VERSION,
        "rule_version": intel.rule_version or RULE_VERSION,
        "learning_version": LEARNING_VERSION,
        "generated_by": generated_by,
        "generated_at": datetime.utcnow().isoformat(),
        "recommendedProduct": product_rec["primary"],
        "messageDirection": message_rec["primary"],
        "campaignPriority": priority_label,
        "expectedRevenue": revenue_pred["expected_revenue"],
        "expectedConversion": conversion_pred["expected_conversion"],
        "analyzer": {
            "customer_intelligence_score": analysis["customer_intelligence_score"],
            "confidence_score": analysis["confidence_score"],
            "confidence_category": confidence_category(analysis["confidence_score"]),
            "recommendation_context": analysis["recommendation_context"],
        },
        "product": product_rec,
        "message": message_rec,
        "campaign": campaign_rec,
        "geographic": geo_rec,
        "revenue_prediction": revenue_pred,
        "conversion_prediction": conversion_pred,
        "scores": scores,
        "business_priority": business_priority,
        "campaign_readiness": readiness,
        "explanation": {
            "summary": reason_text,
            "business_rules_used": rules_used,
            "recommendation_rationale": analysis.get("recommendation_rationale"),
        },
        "audit": {
            "rule_version": intel.rule_version or RULE_VERSION,
            "learning_version": LEARNING_VERSION,
            "engine_version": ENGINE_VERSION,
            "confidence": product_rec["confidence"],
            "reason": reason_text,
            "generated_by": generated_by,
            "business_rules_used": rules_used,
            "recommendation_rationale": analysis.get("recommendation_rationale"),
        },
    }

    _persist_recommendation(db, customer.customer_id, payload, product_rec, message_rec, campaign_rec, reason_text)
    return payload


def _persist_recommendation(
    db: Session,
    customer_id: uuid.UUID,
    payload: dict,
    product_rec: dict,
    message_rec: dict,
    campaign_rec: dict,
    reason: str,
) -> Recommendation:
    existing = (
        db.query(Recommendation)
        .filter(Recommendation.customer_id == customer_id)
        .order_by(Recommendation.generated_at.desc())
        .first()
    )
    fields = {
        "recommended_product": product_rec["primary"],
        "recommended_message": message_rec["primary"],
        "recommended_campaign": campaign_rec["recommended_campaign"],
        "confidence_score": product_rec["confidence"],
        "reason": reason,
        "rule_version": payload["rule_version"],
        "learning_version": payload["learning_version"],
        "engine_version": payload["engine_version"],
        "generated_by": payload["generated_by"],
        "ranking_json": json.dumps(product_rec["ranking"]),
        "scores_json": json.dumps(payload["scores"]),
        "audit_json": json.dumps(payload["audit"]),
        "generated_at": datetime.utcnow(),
    }
    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        db.flush()
        payload["recommendation_id"] = str(existing.recommendation_id)
        return existing

    row = Recommendation(customer_id=customer_id, **fields)
    db.add(row)
    db.flush()
    payload["recommendation_id"] = str(row.recommendation_id)
    return row


def get_ai_recommendation(db: Session, customer_id: str, *, regenerate: bool = False) -> dict | None:
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
    customer, intel = row

    rec = db.query(Recommendation).filter(Recommendation.customer_id == cid).order_by(Recommendation.generated_at.desc()).first()
    if regenerate or not rec or not rec.audit_json:
        payload = run_ai_recommendation_for_intelligence(db, customer, intel)
        db.commit()
        return payload

    try:
        audit = json.loads(rec.audit_json)
        scores = json.loads(rec.scores_json or "{}")
        ranking = json.loads(rec.ranking_json or "[]")
    except json.JSONDecodeError:
        return run_ai_recommendation_for_intelligence(db, customer, intel)

    rationale = audit.get("recommendation_rationale") or rationale_from_intelligence_row(intel, customer)

    return {
        "recommendation_id": str(rec.recommendation_id),
        "customer_id": customer_id,
        "engine_version": rec.engine_version or ENGINE_VERSION,
        "rule_version": rec.rule_version,
        "learning_version": rec.learning_version,
        "generated_by": rec.generated_by,
        "generated_at": rec.generated_at.isoformat() if rec.generated_at else None,
        "recommendedProduct": rec.recommended_product,
        "messageDirection": rec.recommended_message,
        "campaignPriority": _index_level(intel.campaign_priority),
        "expectedRevenue": intel.expected_revenue,
        "expectedConversion": intel.expected_conversion,
        "product": {
            "primary": rec.recommended_product,
            "ranking": ranking,
            "confidence": rec.confidence_score,
            "confidence_category": confidence_category(rec.confidence_score),
            "reason": (rec.reason or "").split("; ") if rec.reason else [],
        },
        "message": {"primary": rec.recommended_message, "confidence": rec.confidence_score},
        "campaign": {"recommended_campaign": rec.recommended_campaign, "confidence": rec.confidence_score},
        "geographic": {
            "recommended_state": customer.state,
            "recommended_zip": customer.zip,
        },
        "revenue_prediction": {
            "expected_revenue": intel.expected_revenue,
            "revenue_range": {
                "low": round((intel.expected_revenue or 0) * 0.85, 2),
                "high": round((intel.expected_revenue or 0) * 1.15, 2),
            },
            "confidence": rec.confidence_score,
            "confidence_category": confidence_category(rec.confidence_score),
            "forecast_interval": "conservative",
        },
        "conversion_prediction": {
            "expected_conversion": intel.expected_conversion,
            "campaign_priority": _index_level(intel.campaign_priority),
        },
        "scores": scores,
        "business_priority": _business_priority(scores, _index_level(intel.campaign_priority)),
        "campaign_readiness": _campaign_readiness(
            scores, _business_priority(scores, _index_level(intel.campaign_priority))
        ),
        "explanation": {
            "summary": rec.reason,
            "business_rules_used": audit.get("business_rules_used") or list(DASHBOARD_RULE_MAP.values())[:4],
            "recommendation_rationale": rationale,
        },
        "audit": audit,
    }
