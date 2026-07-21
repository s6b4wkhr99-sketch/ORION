"""Phase 1 — Tiered intelligence trace storage (summary in-row, full trace on demand)."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.customer import Customer, CustomerIntelligence
from app.models.intelligence_version import IntelligenceVersion
from app.models.scale import IntelligenceTrace

BATCH_FLUSH_ROWS = 100
BATCH_COMMIT_ROWS = 1000


def build_trace_summary(rule_trace: list[dict[str, Any]], framework: dict[str, Any] | None = None) -> dict[str, Any]:
    rule_ids: list[str] = []
    business_rule_ids: list[str] = []
    explanations: list[str] = []
    for item in rule_trace:
        if item.get("rule_id"):
            rule_ids.append(str(item["rule_id"]))
        if item.get("business_rule_id"):
            business_rule_ids.append(str(item["business_rule_id"]))
        if item.get("explanation"):
            explanations.append(str(item["explanation"]))

    confidences: list[float] = []
    if framework:
        for cat in framework.get("categories", {}).values():
            if isinstance(cat, dict) and cat.get("confidence") is not None:
                confidences.append(float(cat["confidence"]))

    return {
        "rule_ids": rule_ids,
        "business_rule_ids": list(dict.fromkeys(business_rule_ids)),
        "rule_count": len(rule_ids),
        "confidence": round(sum(confidences) / len(confidences), 4) if confidences else None,
        "summary": explanations[-1] if explanations else "Customer intelligence calculated",
    }


def build_framework_summary(framework: dict[str, Any]) -> dict[str, Any]:
    categories: dict[str, Any] = {}
    for name, cat in framework.get("categories", {}).items():
        if not isinstance(cat, dict):
            continue
        categories[name] = {
            "score": cat.get("score"),
            "level": cat.get("level"),
            "confidence": cat.get("confidence"),
            "explanation": cat.get("explanation"),
        }
        if name == "recommendation":
            if cat.get("selection_rule"):
                categories[name]["selection_rule"] = cat.get("selection_rule")
            if cat.get("rationale_summary"):
                categories[name]["rationale_summary"] = cat.get("rationale_summary")
            # Full rationale stored once at summary root — not duplicated in categories.
        if name == "sleep_affinity":
            if cat.get("sleep_segment"):
                categories[name]["sleep_segment"] = cat.get("sleep_segment")
            if cat.get("sleep_geo_boost") is not None:
                categories[name]["sleep_geo_boost"] = cat.get("sleep_geo_boost")
    audit = framework.get("audit", {}) if isinstance(framework.get("audit"), dict) else {}
    rec_cat = categories.get("recommendation") if isinstance(categories.get("recommendation"), dict) else {}
    rationale = rec_cat.get("rationale") or framework.get("recommendation_rationale")
    summary_payload: dict[str, Any] = {
        "calculation_id": framework.get("calculation_id"),
        "calculation_version": framework.get("calculation_version"),
        "engine_version": framework.get("engine_version"),
        "categories": categories,
        "audit": {
            "rule_version": audit.get("rule_version"),
            "timestamp": audit.get("timestamp"),
        },
    }
    if rationale:
        summary_payload["recommendation_rationale"] = rationale
    return summary_payload


def _intelligence_scalar_payload(result: dict[str, Any], trace_summary: dict, framework_summary: dict) -> dict[str, Any]:
    return {
        "prizm_proxy_segment": result["prizm_proxy_segment"],
        "ceragem_segment": result["ceragem_segment"],
        "message_direction": result["message_direction"],
        "pain_index": result["pain_index"],
        "purchase_power_index": result["purchase_power_index"],
        "lifestyle_index": result["lifestyle_index"],
        "email_response_index": result["email_responsiveness_index"],
        "brand_familiarity_index": result["brand_familiarity_index"],
        "recommended_product": result["recommended_product"],
        "expected_conversion": result["expected_conversion_rate"],
        "baseline_conversion": result.get("baseline_conversion"),
        "promo_uplift": result.get("promo_uplift"),
        "baseline_revenue": result.get("baseline_revenue"),
        "expected_revenue": result["expected_revenue"],
        "campaign_priority": result["campaign_priority_score"],
        "price_resistance_score": result.get("price_resistance_score"),
        "recommended_promotion": result.get("recommended_promotion"),
        "promo_code": result.get("promo_code"),
        "commercial_version": result.get("commercial_version"),
        "trace_json": None,
        "framework_json": None,
        "trace_summary_json": json.dumps(trace_summary),
        "framework_summary_json": json.dumps(framework_summary),
        "calculation_version": result.get("calculation_version"),
        "engine_version": result.get("engine_version"),
        "generated_by": "upload_pipeline",
    }


def _upsert_full_trace(db: Session, customer_id, rule_trace: list, framework: dict) -> None:
    trace_row = db.query(IntelligenceTrace).filter(IntelligenceTrace.customer_id == customer_id).first()
    payload = {
        "trace_json": json.dumps(rule_trace),
        "framework_json": json.dumps(framework),
    }
    if trace_row:
        for key, value in payload.items():
            setattr(trace_row, key, value)
    else:
        db.add(IntelligenceTrace(customer_id=customer_id, **payload))


def persist_intelligence_result(
    db: Session,
    customer: Customer,
    result: dict[str, Any],
    *,
    store_full_trace: bool = True,
    record_versions: bool = True,
    sync_recommendation: bool = True,
    generated_by: str = "upload_pipeline",
) -> CustomerIntelligence:
    """Store scalar intelligence + compact summaries; full trace in intelligence_trace."""
    rule_trace = result.get("rule_trace", [])
    framework = result.get("framework", {})
    trace_summary = build_trace_summary(rule_trace, framework)
    framework_summary = build_framework_summary(framework)
    payload = _intelligence_scalar_payload(result, trace_summary, framework_summary)

    intel = db.query(CustomerIntelligence).filter(CustomerIntelligence.customer_id == customer.customer_id).first()
    if intel:
        if record_versions:
            last_version = (
                db.query(IntelligenceVersion.version)
                .filter(IntelligenceVersion.customer_id == customer.customer_id)
                .order_by(IntelligenceVersion.version.desc())
                .first()
            )
            next_version = (last_version[0] if last_version else 0) + 1
            snapshot = {k: getattr(intel, k) for k in payload if hasattr(intel, k)}
            snapshot["trace_json"] = None
            snapshot["framework_json"] = None
            db.add(
                IntelligenceVersion(
                    customer_id=customer.customer_id,
                    version=next_version,
                    intelligence_json=json.dumps(snapshot, default=str),
                    source_upload_id=customer.upload_id,
                )
            )
        for key, value in payload.items():
            setattr(intel, key, value)
        row = intel
    else:
        row = CustomerIntelligence(customer_id=customer.customer_id, **payload)
        db.add(row)

    if store_full_trace:
        _upsert_full_trace(db, customer.customer_id, rule_trace, framework)

    from app.schema.triggers import stamp_intelligence_generated, sync_recommendation_from_intelligence

    stamp_intelligence_generated(
        row,
        calculation_version=result.get("calculation_version"),
        engine_version=result.get("engine_version"),
        generated_by=result.get("generated_by") or generated_by,
    )
    if sync_recommendation:
        sync_recommendation_from_intelligence(db, row)
    return row


def load_full_trace(db: Session, customer_id) -> tuple[list, dict]:
    row = db.query(IntelligenceTrace).filter(IntelligenceTrace.customer_id == customer_id).first()
    if not row:
        return [], {}
    trace: list = []
    framework: dict = {}
    if row.trace_json:
        try:
            trace = json.loads(row.trace_json)
        except json.JSONDecodeError:
            trace = []
    if row.framework_json:
        try:
            framework = json.loads(row.framework_json)
        except json.JSONDecodeError:
            framework = {}
    return trace, framework


def load_framework_for_row(db: Session, intel: CustomerIntelligence) -> dict | None:
    import json

    if getattr(intel, "framework_summary_json", None):
        try:
            summary = json.loads(intel.framework_summary_json)
            if summary:
                return summary
        except json.JSONDecodeError:
            pass
    if getattr(intel, "framework_json", None):
        try:
            return json.loads(intel.framework_json)
        except json.JSONDecodeError:
            pass
    _, framework = load_full_trace(db, intel.customer_id)
    return framework or None
