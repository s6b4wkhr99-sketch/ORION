"""Volume 21 — Master index and knowledge governance service."""

from __future__ import annotations

import importlib
from pathlib import Path

from sqlalchemy.orm import Session

from app.knowledge.registry import (
    API_CROSS_REFERENCE,
    BUSINESS_RULE_CROSS_REFERENCE,
    COMPONENT_LIBRARY,
    DASHBOARD_CROSS_REFERENCE,
    DATABASE_CROSS_REFERENCE,
    DATA_SOURCE_INDEX,
    DOCUMENTATION_DEPENDENCY_MAP,
    DOCUMENTATION_GOVERNANCE_REQUIREMENTS,
    DOCUMENTATION_STRUCTURE,
    DOCUMENT_VOLUMES,
    EXECUTIVE_KPI_INDEX,
    GLOSSARY,
    INTELLIGENCE_CROSS_REFERENCE,
    KNOWLEDGE_OWNER,
    KNOWLEDGE_VERSION,
    MASTER_ACCEPTANCE_CRITERIA,
    MASTER_NAVIGATION,
    PROVIDER_INDEX,
    VERSION_GOVERNANCE_FIELDS,
    WORKFLOW_CROSS_REFERENCE,
)
from app.methodology.registry import INTELLIGENCE_LAYERS
from app.rules.library import RULES
from app.schema.registry import TABLE_MAP


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _approved_doc_paths() -> list[Path]:
    root = _project_root()
    paths: list[Path] = [root / "docs" / "README.md"]
    for doc in DOCUMENT_VOLUMES:
        if doc["status"] == "approved":
            paths.append(root / doc["file"])
    return paths


def _collect_router_paths() -> set[str]:
    from app.api.v1.router import router

    paths: set[str] = set()
    for route in router.routes:
        if not hasattr(route, "methods") or not hasattr(route, "path"):
            continue
        paths.add(route.path)
    return paths


def get_knowledge_overview(db: Session | None = None) -> dict:
    status = _implementation_status(db) if db else {}
    return {
        "knowledgeVersion": KNOWLEDGE_VERSION,
        "knowledgeOwner": KNOWLEDGE_OWNER,
        "documentationStructure": DOCUMENTATION_STRUCTURE,
        "masterNavigation": list(MASTER_NAVIGATION),
        "documentationDependencyMap": list(DOCUMENTATION_DEPENDENCY_MAP),
        "documentVolumes": list(DOCUMENT_VOLUMES),
        "databaseCrossReference": list(DATABASE_CROSS_REFERENCE),
        "intelligenceCrossReference": list(INTELLIGENCE_CROSS_REFERENCE),
        "businessRuleCrossReference": list(BUSINESS_RULE_CROSS_REFERENCE),
        "dashboardCrossReference": list(DASHBOARD_CROSS_REFERENCE),
        "apiCrossReference": list(API_CROSS_REFERENCE),
        "workflowCrossReference": list(WORKFLOW_CROSS_REFERENCE),
        "componentLibrary": list(COMPONENT_LIBRARY),
        "providerIndex": list(PROVIDER_INDEX),
        "dataSourceIndex": list(DATA_SOURCE_INDEX),
        "executiveKpiIndex": list(EXECUTIVE_KPI_INDEX),
        "glossary": list(GLOSSARY),
        "versionGovernanceFields": list(VERSION_GOVERNANCE_FIELDS),
        "documentationGovernanceRequirements": list(DOCUMENTATION_GOVERNANCE_REQUIREMENTS),
        "masterAcceptanceCriteria": list(MASTER_ACCEPTANCE_CRITERIA),
        "methodologyLayers": list(INTELLIGENCE_LAYERS),
        "ruleCount": len(RULES),
        "tableCount": len(TABLE_MAP),
        "implementationStatus": status,
    }


def get_knowledge_index() -> dict:
    return {
        "documentVolumes": list(DOCUMENT_VOLUMES),
        "masterNavigation": list(MASTER_NAVIGATION),
        "documentationDependencyMap": list(DOCUMENTATION_DEPENDENCY_MAP),
    }


def get_knowledge_cross_reference() -> dict:
    return {
        "database": list(DATABASE_CROSS_REFERENCE),
        "intelligence": list(INTELLIGENCE_CROSS_REFERENCE),
        "businessRules": list(BUSINESS_RULE_CROSS_REFERENCE),
        "dashboards": list(DASHBOARD_CROSS_REFERENCE),
        "apis": list(API_CROSS_REFERENCE),
        "workflows": list(WORKFLOW_CROSS_REFERENCE),
    }


def get_knowledge_governance() -> dict:
    return {
        "versionGovernanceFields": list(VERSION_GOVERNANCE_FIELDS),
        "documentationGovernanceRequirements": list(DOCUMENTATION_GOVERNANCE_REQUIREMENTS),
        "masterAcceptanceCriteria": list(MASTER_ACCEPTANCE_CRITERIA),
        "version": KNOWLEDGE_VERSION,
    }


def get_knowledge_glossary() -> dict:
    return {"glossary": list(GLOSSARY)}


def get_knowledge_acceptance_criteria(db: Session) -> dict:
    status = _implementation_status(db)
    criteria = []
    for item in MASTER_ACCEPTANCE_CRITERIA:
        criteria.append({**item, "status": status.get(item["id"], "implemented")})
    return {"criteria": criteria, "allMet": all(c["status"] == "implemented" for c in criteria)}


def _implementation_status(db: Session) -> dict:
    root = _project_root()
    readme_exists = (root / "docs" / "README.md").is_file()
    docs_indexed = len(DOCUMENT_VOLUMES) == 26 and readme_exists

    rules_traceable = all(r.rule_id and r.implementation_refs for r in RULES)
    rule_categories = {r.category for r in RULES}
    xref_categories = {item["prefix"] for item in BUSINESS_RULE_CROSS_REFERENCE}
    rules_indexed = rule_categories.issuperset(xref_categories)

    spec_tables = {item["table"] for item in DATABASE_CROSS_REFERENCE}
    db_referenced = spec_tables.issubset(set(TABLE_MAP.keys()))

    router_paths = _collect_router_paths()
    api_documented = all(
        any(route.startswith(item["prefix"].replace("/api/v1", "/v1")) for route in router_paths)
        for item in API_CROSS_REFERENCE
    )

    workflows_indexed = len(WORKFLOW_CROSS_REFERENCE) >= 7
    dashboards_linked = all(item.get("api") for item in DASHBOARD_CROSS_REFERENCE)
    intelligence_sourced = all(item.get("volumes") and item.get("module") for item in INTELLIGENCE_CROSS_REFERENCE)

    methodology_implemented = all(item.get("module") for item in INTELLIGENCE_LAYERS)
    provider_modules = importlib.import_module("app.providers.adapter")
    providers_registered = set(provider_modules.ADAPTER_CLASSES.keys()) == {p["provider"] for p in PROVIDER_INDEX}

    dependency_consistent = len(DOCUMENTATION_DEPENDENCY_MAP) >= 10
    approved_on_disk = all(path.is_file() for path in _approved_doc_paths())

    return {
        "AC-01": "implemented" if docs_indexed else "pending_data",
        "AC-02": "implemented" if rules_traceable and rules_indexed else "pending_data",
        "AC-03": "implemented" if db_referenced else "pending_data",
        "AC-04": "implemented" if api_documented else "pending_data",
        "AC-05": "implemented" if workflows_indexed else "pending_data",
        "AC-06": "implemented" if dashboards_linked else "pending_data",
        "AC-07": "implemented" if intelligence_sourced else "pending_data",
        "AC-08": "implemented" if methodology_implemented else "pending_data",
        "AC-09": "implemented" if dependency_consistent and providers_registered and approved_on_disk else "pending_data",
    }
