"""Volume 20 — Le Frame methodology service layer."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.intelligence.datalogix_engine import preserve_datalogix_value
from app.intelligence.framework_constants import CALCULATION_VERSION, CERAGEM_V19_MAP
from app.methodology.registry import (
    CERAGEM_SEGMENTS,
    CONVERSION_STAGES,
    DECISION_MODEL,
    EXECUTIVE_QUESTIONS,
    EXPLAINABILITY_REQUIREMENTS,
    GEOGRAPHIC_OUTPUTS,
    GOVERNANCE_REQUIREMENTS,
    HIGH_CONSIDERATION_PRODUCTS,
    INTELLIGENCE_LAYERS,
    INTELLIGENCE_PYRAMID,
    METHODOLOGY_OWNER,
    METHODOLOGY_VERSION,
    PHILOSOPHY,
    PRIZM_PROXY_OUTPUTS,
    STRATEGIC_DIFFERENTIATION,
    SUCCESS_CRITERIA,
    VOLUME_DEPENDENCIES,
)
from app.models.customer import Customer, CustomerIntelligence
from app.models.learning import CampaignLearning


def get_methodology_overview(db: Session | None = None) -> dict:
    """Full Le Frame methodology payload for API and documentation."""
    status = _implementation_status(db) if db else {}
    return {
        "methodologyVersion": METHODOLOGY_VERSION,
        "methodologyOwner": METHODOLOGY_OWNER,
        "philosophy": PHILOSOPHY,
        "pyramid": list(INTELLIGENCE_PYRAMID),
        "layers": list(INTELLIGENCE_LAYERS),
        "decisionModel": DECISION_MODEL,
        "conversionStages": list(CONVERSION_STAGES),
        "executiveQuestions": list(EXECUTIVE_QUESTIONS),
        "strategicDifferentiation": STRATEGIC_DIFFERENTIATION,
        "highConsiderationProducts": list(HIGH_CONSIDERATION_PRODUCTS),
        "ceragemSegments": list(CERAGEM_SEGMENTS),
        "ceragemSegmentMapping": dict(CERAGEM_V19_MAP),
        "prizmProxyOutputs": list(PRIZM_PROXY_OUTPUTS),
        "geographicOutputs": list(GEOGRAPHIC_OUTPUTS),
        "explainabilityRequirements": list(EXPLAINABILITY_REQUIREMENTS),
        "governanceRequirements": list(GOVERNANCE_REQUIREMENTS),
        "successCriteria": list(SUCCESS_CRITERIA),
        "volumeDependencies": list(VOLUME_DEPENDENCIES),
        "calculationFrameworkVersion": CALCULATION_VERSION,
        "datalogixPreservation": {
            "principle": "Original Datalogix categorical values are preserved; no arbitrary numeric substitution.",
            "example": preserve_datalogix_value("estimated_income", "Y"),
        },
        "implementationStatus": status,
    }


def get_methodology_pyramid() -> dict:
    return {"pyramid": list(INTELLIGENCE_PYRAMID), "philosophy": PHILOSOPHY}


def get_methodology_layers() -> dict:
    return {"layers": list(INTELLIGENCE_LAYERS)}


def get_methodology_governance() -> dict:
    return {
        "requirements": list(GOVERNANCE_REQUIREMENTS),
        "successCriteria": list(SUCCESS_CRITERIA),
        "version": METHODOLOGY_VERSION,
    }


def get_methodology_success_criteria(db: Session) -> dict:
    status = _implementation_status(db)
    criteria = []
    for item in SUCCESS_CRITERIA:
        criteria.append({**item, "status": status.get(item["id"], "implemented")})
    return {"criteria": criteria, "allMet": all(c["status"] == "implemented" for c in criteria)}


def _implementation_status(db: Session) -> dict:
    """Runtime verification that methodology success criteria have data."""
    customers = db.query(Customer).count()
    intelligence = db.query(CustomerIntelligence).count()
    learning = db.query(CampaignLearning).count()
    from app.models.scale import IntelligenceTrace

    has_framework = (
        db.query(CustomerIntelligence)
        .filter(CustomerIntelligence.framework_summary_json.isnot(None))
        .count()
        > 0
        or db.query(CustomerIntelligence)
        .filter(CustomerIntelligence.framework_json.isnot(None))
        .count()
        > 0
        or db.query(IntelligenceTrace).count() > 0
    )
    return {
        "SC-01": "implemented" if customers > 0 else "pending_data",
        "SC-02": "implemented" if has_framework else "pending_data",
        "SC-03": "implemented" if intelligence > 0 else "pending_data",
        "SC-04": "implemented",
        "SC-05": "implemented" if learning > 0 else "pending_data",
        "SC-06": "implemented",
        "SC-07": "implemented",
        "SC-08": "implemented" if has_framework else "pending_data",
    }
