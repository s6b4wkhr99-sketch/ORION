"""Volume 25 — Git Workflow & Release Management."""

from app.git_workflow.registry import GIT_WORKFLOW_VERSION
from app.git_workflow.service import get_git_workflow_overview, verify_git_workflow_compliance

__all__ = [
    "GIT_WORKFLOW_VERSION",
    "get_git_workflow_overview",
    "verify_git_workflow_compliance",
]
