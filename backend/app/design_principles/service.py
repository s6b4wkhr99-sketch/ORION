"""Volume 26 — CIOS Design Principles service."""

from __future__ import annotations

import os
from pathlib import Path

from app.design_principles.registry import (
    AUDIT_QUESTIONS,
    AUTOMATION_EXAMPLES,
    CANONICAL_DEFINITIONS,
    CONSTITUTION,
    DESIGN_PRINCIPLES_ACCEPTANCE_CRITERIA,
    DESIGN_PRINCIPLES_SCOPE,
    DESIGN_PRINCIPLES_VERSION,
    DETERMINISTIC_DOMAINS,
    EXPLAINABILITY_FIELDS,
    FINAL_STATEMENT,
    HIGH_CONSIDERATION_ATTRIBUTES,
    INTELLIGENCE_VERSION_FIELDS,
    METADATA_DRIVEN_EXAMPLES,
    NO_HARD_CODING_EXAMPLES,
    PRINCIPLES,
    SECURITY_CAPABILITIES,
    VISION,
)


def get_design_principles_overview() -> dict:
    return {
        "designPrinciplesVersion": DESIGN_PRINCIPLES_VERSION,
        "scope": DESIGN_PRINCIPLES_SCOPE,
        "vision": VISION,
        "principles": list(PRINCIPLES),
        "metadataDrivenExamples": list(METADATA_DRIVEN_EXAMPLES),
        "noHardCodingExamples": list(NO_HARD_CODING_EXAMPLES),
        "canonicalDefinitions": list(CANONICAL_DEFINITIONS),
        "deterministicDomains": list(DETERMINISTIC_DOMAINS),
        "automationExamples": list(AUTOMATION_EXAMPLES),
        "highConsiderationAttributes": list(HIGH_CONSIDERATION_ATTRIBUTES),
        "securityCapabilities": list(SECURITY_CAPABILITIES),
        "auditQuestions": list(AUDIT_QUESTIONS),
        "explainabilityFields": list(EXPLAINABILITY_FIELDS),
        "intelligenceVersionFields": list(INTELLIGENCE_VERSION_FIELDS),
        "constitution": list(CONSTITUTION),
        "finalStatement": FINAL_STATEMENT,
        "acceptanceCriteria": list(DESIGN_PRINCIPLES_ACCEPTANCE_CRITERIA),
    }


def verify_design_principles_compliance(project_root: str) -> dict:
    root = Path(project_root)
    backend = root / "backend" / "app"

    checks = {
        "customerIntelligenceFirst": (backend / "intelligence").is_dir(),
        "intelligenceBeforeCampaign": (backend / "campaign").is_dir() and (backend / "intelligence").is_dir(),
        "explainableRecommendations": (backend / "ai_engine").is_dir() and (backend / "rules" / "library.py").is_file(),
        "rawDataImmutablePolicy": (backend / "acquisition" / "upload.py").is_file(),
        "intelligenceVersioned": (backend / "intelligence" / "calculation_framework.py").is_file(),
        "businessRulesBeforeAi": (backend / "rules" / "library.py").is_file(),
        "metadataDriven": (backend / "reference" / "registry.py").is_file(),
        "noHardCodingPolicy": (backend / "conventions" / "registry.py").is_file(),
        "oneDefinitionOnly": (backend / "mapping" / "data_dictionary.py").is_file(),
        "deterministicProcessing": (backend / "intelligence" / "calculation_framework.py").is_file(),
        "learningImprovesFuture": (backend / "ai_engine").is_dir(),
        "dashboardsAreIntelligence": (backend / "analytics").is_dir(),
        "geographyIsIntelligence": (backend / "reference" / "registry.py").is_file(),
        "securityBuiltIn": (backend / "security").is_dir(),
        "actionsAuditable": (backend / "security" / "audit.py").is_file() or (backend / "models" / "audit.py").is_file(),
        "executiveDecisionSupport": (backend / "analytics").is_dir(),
        "documentationEqualsCode": (root / "docs" / "26_CIOS_Design_Principles.md").is_file(),
        "automationByDefault": (backend / "mapping" / "auto_engine.py").is_file(),
        "platformArchitecture": (backend / "providers").is_dir() and (backend / "dashboard").is_dir(),
        "principlesRegistryPresent": (backend / "design_principles" / "registry.py").is_file(),
        "acceptanceTestsPresent": os.path.isfile(os.path.join(project_root, "backend", "tests", "test_volume26_acceptance.py")),
    }

    principle_count = len(PRINCIPLES)
    implemented_count = sum(1 for value in checks.values() if value)

    return {
        **checks,
        "principleCount": principle_count,
        "architecturalAlignmentScore": f"{implemented_count}/{len(checks)}",
        "allPrinciplesDocumented": principle_count == 23,
        "constitutionDocumented": len(CONSTITUTION) == 4,
        "volume26Documented": checks["documentationEqualsCode"],
    }
