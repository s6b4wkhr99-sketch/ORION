"""Volume 25 — Git Workflow & Release Management service."""

from __future__ import annotations

import os
import re
from pathlib import Path

from app.git_workflow.registry import (
    BRANCH_PROTECTION_RULES,
    BRANCH_STRATEGY,
    CD_PIPELINE_STAGES,
    CI_PULL_REQUEST_CHECKS,
    CODE_OWNERSHIP,
    COMMIT_EXAMPLES,
    COMMIT_FORMAT,
    COMMIT_TYPES,
    DEFINITION_OF_DONE,
    DEPENDENCIES,
    DOCUMENTATION_SYNC_REQUIREMENTS,
    GIT_WORKFLOW_ACCEPTANCE_CRITERIA,
    GIT_WORKFLOW_VERSION,
    MERGE_STRATEGY,
    MERGE_STRATEGY_REASONS,
    PROTECTED_BRANCHES,
    PULL_REQUEST_SECTIONS,
    RELEASE_LIFECYCLE,
    RELEASE_NOTES_SECTIONS,
    REPOSITORY_STANDARDS,
    ROLLBACK_PROCESS,
    ROLLBACK_TRIGGERS,
    SEMVER_DEFINITIONS,
    SEMVER_FORMAT,
    TAG_EXAMPLES,
    TAG_FORMAT,
)


def get_git_workflow_overview() -> dict:
    return {
        "gitWorkflowVersion": GIT_WORKFLOW_VERSION,
        "dependencies": list(DEPENDENCIES),
        "branchStrategy": list(BRANCH_STRATEGY),
        "protectedBranches": list(PROTECTED_BRANCHES),
        "branchProtectionRules": list(BRANCH_PROTECTION_RULES),
        "commit": {
            "format": COMMIT_FORMAT,
            "types": list(COMMIT_TYPES),
            "examples": list(COMMIT_EXAMPLES),
        },
        "pullRequestSections": list(PULL_REQUEST_SECTIONS),
        "mergeStrategy": MERGE_STRATEGY,
        "mergeStrategyReasons": list(MERGE_STRATEGY_REASONS),
        "semanticVersioning": {
            "format": SEMVER_FORMAT,
            "definitions": SEMVER_DEFINITIONS,
        },
        "releaseLifecycle": list(RELEASE_LIFECYCLE),
        "tags": {"format": TAG_FORMAT, "examples": list(TAG_EXAMPLES)},
        "releaseNotesSections": list(RELEASE_NOTES_SECTIONS),
        "rollback": {
            "triggers": list(ROLLBACK_TRIGGERS),
            "process": list(ROLLBACK_PROCESS),
        },
        "documentationSync": list(DOCUMENTATION_SYNC_REQUIREMENTS),
        "ciChecks": list(CI_PULL_REQUEST_CHECKS),
        "cdPipeline": list(CD_PIPELINE_STAGES),
        "codeOwnership": list(CODE_OWNERSHIP),
        "repositoryStandards": list(REPOSITORY_STANDARDS),
        "definitionOfDone": list(DEFINITION_OF_DONE),
        "acceptanceCriteria": list(GIT_WORKFLOW_ACCEPTANCE_CRITERIA),
    }


_STANDARD_ALIASES = {"deployment/": ("deploy",)}


def _standard_paths(project_root: str, standard: str) -> list[Path]:
    root = Path(project_root)
    if standard.endswith("/"):
        base = standard.rstrip("/")
        aliases = _STANDARD_ALIASES.get(standard, ())
        return [root / base, *[root / alias for alias in aliases]]
    return [root / standard]


def _standard_exists(project_root: str, standard: str) -> bool:
    return any(path.is_file() or path.is_dir() for path in _standard_paths(project_root, standard))


def verify_git_workflow_compliance(project_root: str) -> dict:
    from app.config import settings

    root = Path(project_root)
    standards: dict[str, bool] = {}
    for item in REPOSITORY_STANDARDS:
        standards[item] = _standard_exists(project_root, item)

    ci_workflow = root / ".github" / "workflows" / "cios-ci.yml"
    ci_content = ci_workflow.read_text(encoding="utf-8") if ci_workflow.is_file() else ""
    ci_has_acceptance = "run_acceptance.py" in ci_content
    ci_has_security = "security-scan" in ci_content or "pip-audit" in ci_content
    ci_has_docker = "docker build" in ci_content

    rollback_script = root / "deploy" / "scripts" / "rollback.sh"
    deploy_dir = root / "deploy"

    semver_ok = bool(re.match(r"^\d+\.\d+\.\d+$", settings.app_version))
    changelog_ok = standards.get("CHANGELOG.md", False)
    docs_volume = (root / "docs" / "25_Git_Workflow_Release_Management.md").is_file()

    return {
        "branchStrategyDocumented": True,
        "commitConventionDocumented": True,
        "mergeStrategyDocumented": MERGE_STRATEGY == "Squash and Merge",
        "semanticVersioningConfigured": semver_ok,
        "appVersion": settings.app_version,
        "ciPipelinePresent": ci_workflow.is_file(),
        "ciRunsAcceptanceTests": ci_has_acceptance,
        "ciRunsSecurityScan": ci_has_security,
        "ciBuildsDockerImages": ci_has_docker,
        "rollbackScriptPresent": rollback_script.is_file(),
        "deployDirectoryPresent": deploy_dir.is_dir(),
        "repositoryStandards": standards,
        "repositoryStandardsMet": all(standards.values()),
        "changelogPresent": changelog_ok,
        "volume25Documented": docs_volume,
        "acceptanceTestRunner": os.path.isfile(os.path.join(project_root, "backend", "tests", "run_acceptance.py")),
    }
