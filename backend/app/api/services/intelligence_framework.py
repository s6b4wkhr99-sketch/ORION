"""Volume 19 — Intelligence calculation framework API services."""

import json
import uuid

from sqlalchemy.orm import Session

from app.intelligence.calculation_framework import framework_from_intelligence_row
from app.intelligence.framework_constants import INTELLIGENCE_CATEGORIES
from app.intelligence.recommendation_rationale import rationale_from_framework_summary, rationale_from_intelligence_row
from app.intelligence.trace_storage import load_full_trace
from app.models.customer import Customer, CustomerIntelligence


def get_intelligence_framework(db: Session, customer_id: str) -> dict | None:
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
    framework = framework_from_intelligence_row(intel, db=db)
    if not framework:
        return None

    rationale = rationale_from_framework_summary(framework)
    if not rationale:
        rationale = rationale_from_intelligence_row(intel, customer)

    trace, _ = load_full_trace(db, intel.customer_id)
    if not trace and intel.trace_json:
        try:
            trace = json.loads(intel.trace_json)
        except json.JSONDecodeError:
            trace = []

    return {
        "customerId": customer_id,
        "calculationId": framework.get("calculation_id"),
        "calculationVersion": intel.calculation_version or framework.get("calculation_version"),
        "engineVersion": intel.engine_version or framework.get("engine_version"),
        "ruleVersion": intel.rule_version,
        "generatedBy": intel.generated_by,
        "generatedAt": intel.generated_at.isoformat() if intel.generated_at else None,
        "categories": framework.get("categories", {}),
        "audit": framework.get("audit", {}),
        "intelligenceCategories": list(INTELLIGENCE_CATEGORIES),
        "ruleTrace": trace,
        "recommendationRationale": rationale,
    }


def get_customer_intelligence_with_framework(db: Session, customer_id: str) -> dict | None:
    from app.api.services.customers import get_customer_intelligence

    base = get_customer_intelligence(db, customer_id)
    if not base:
        return None
    framework = get_intelligence_framework(db, customer_id)
    if framework:
        base["framework"] = {
            "calculationVersion": framework["calculationVersion"],
            "categories": {
                name: {
                    "score": cat.get("score"),
                    "level": cat.get("level"),
                    "confidence": cat.get("confidence"),
                    "explanation": cat.get("explanation"),
                }
                for name, cat in framework.get("categories", {}).items()
            },
        }
        if framework.get("recommendationRationale"):
            base["recommendationRationale"] = framework["recommendationRationale"]
    return base
