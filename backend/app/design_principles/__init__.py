"""Volume 26 — CIOS Design Principles (Project Constitution)."""

from app.design_principles.registry import DESIGN_PRINCIPLES_VERSION
from app.design_principles.service import get_design_principles_overview, verify_design_principles_compliance

__all__ = [
    "DESIGN_PRINCIPLES_VERSION",
    "get_design_principles_overview",
    "verify_design_principles_compliance",
]
