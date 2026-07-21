"""Volume 21 — Master index and knowledge governance."""

from app.knowledge.registry import (
    API_CROSS_REFERENCE,
    BUSINESS_RULE_CROSS_REFERENCE,
    DATABASE_CROSS_REFERENCE,
    DOCUMENT_VOLUMES,
    GLOSSARY,
    INTELLIGENCE_CROSS_REFERENCE,
    KNOWLEDGE_VERSION,
    MASTER_ACCEPTANCE_CRITERIA,
    MASTER_NAVIGATION,
)
from app.knowledge.service import (
    get_knowledge_acceptance_criteria,
    get_knowledge_cross_reference,
    get_knowledge_glossary,
    get_knowledge_governance,
    get_knowledge_index,
    get_knowledge_overview,
)

__all__ = [
    "API_CROSS_REFERENCE",
    "BUSINESS_RULE_CROSS_REFERENCE",
    "DATABASE_CROSS_REFERENCE",
    "DOCUMENT_VOLUMES",
    "GLOSSARY",
    "INTELLIGENCE_CROSS_REFERENCE",
    "KNOWLEDGE_VERSION",
    "MASTER_ACCEPTANCE_CRITERIA",
    "MASTER_NAVIGATION",
    "get_knowledge_acceptance_criteria",
    "get_knowledge_cross_reference",
    "get_knowledge_glossary",
    "get_knowledge_governance",
    "get_knowledge_index",
    "get_knowledge_overview",
]
