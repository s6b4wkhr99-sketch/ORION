"""Volume 25 — Git Workflow & Release Management acceptance tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.git_workflow.registry import (
    BRANCH_STRATEGY,
    COMMIT_TYPES,
    DEFINITION_OF_DONE,
    GIT_WORKFLOW_ACCEPTANCE_CRITERIA,
    GIT_WORKFLOW_VERSION,
    MERGE_STRATEGY,
    PROTECTED_BRANCHES,
    RELEASE_LIFECYCLE,
)
from app.git_workflow.service import get_git_workflow_overview, verify_git_workflow_compliance
from app.main import app
from app.models import *  # noqa: F401, F403
from app.processing.seed import seed_configuration
from app.schema.apply import apply_physical_schema
from app.schema.seed_v16 import seed_v16_reference_schema
from app.security.users import seed_users

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    apply_physical_schema(engine)
    db = SessionLocal()
    seed_configuration(db)
    seed_users(db)
    seed_v16_reference_schema(db)
    db.close()


def _ok(resp):
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("success") is True, body
    return body["data"]


def run_tests():
    _reset()
    passed = 0

    overview = get_git_workflow_overview()
    assert overview["gitWorkflowVersion"] == GIT_WORKFLOW_VERSION
    assert len(overview["branchStrategy"]) == len(BRANCH_STRATEGY)
    assert overview["mergeStrategy"] == MERGE_STRATEGY
    assert len(overview["commit"]["types"]) == len(COMMIT_TYPES)
    assert len(overview["releaseLifecycle"]) == len(RELEASE_LIFECYCLE)
    print("✓ Sections 2–9 Branch strategy, commits, merge and release registry")
    passed += 1

    assert PROTECTED_BRANCHES == ("main", "develop")
    assert len(DEFINITION_OF_DONE) == 9
    assert len(GIT_WORKFLOW_ACCEPTANCE_CRITERIA) == 9
    print("✓ Sections 4, 18–19 Protection, DoD and acceptance criteria")
    passed += 1

    compliance = verify_git_workflow_compliance(PROJECT_ROOT)
    assert compliance["branchStrategyDocumented"] is True
    assert compliance["semanticVersioningConfigured"] is True
    assert compliance["ciPipelinePresent"] is True
    assert compliance["ciRunsAcceptanceTests"] is True
    assert compliance["rollbackScriptPresent"] is True
    assert compliance["repositoryStandardsMet"] is True
    assert compliance["volume25Documented"] is True
    print("✓ Sections 12–17 Repository and CI/CD compliance checks")
    passed += 1

    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"email": "user@company.com", "password": "Ceragem2026!Adm"})
    headers = {"Authorization": f"Bearer {login.json()['data']['token']}"}

    api_overview = _ok(client.get("/api/v1/git-workflow", headers=headers))
    assert api_overview["commit"]["format"] == "type(scope): description"
    assert len(api_overview["codeOwnership"]) == 7
    assert api_overview["tags"]["format"] == "v{Major}.{Minor}.{Patch}"
    print("✓ Git workflow API")
    passed += 1

    api_compliance = _ok(client.get("/api/v1/git-workflow/compliance", headers=headers))
    assert api_compliance["appVersion"] == settings.app_version
    assert api_compliance["changelogPresent"] is True
    print("✓ Git workflow compliance API")
    passed += 1

    doc = os.path.join(PROJECT_ROOT, "docs", "25_Git_Workflow_Release_Management.md")
    changelog = os.path.join(PROJECT_ROOT, "CHANGELOG.md")
    ci_workflow = os.path.join(PROJECT_ROOT, ".github", "workflows", "cios-ci.yml")
    assert os.path.isfile(doc)
    assert os.path.isfile(changelog)
    assert os.path.isfile(ci_workflow)
    print("✓ Documentation, changelog and CI workflow artifacts")
    passed += 1

    print(f"\nVolume 25 Git Workflow & Release Management: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
