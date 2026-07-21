"""Volume 17 — Analytics & Executive Intelligence package."""

from app.analytics.executive import get_executive_intelligence
from app.analytics.insights import generate_business_insights
from app.analytics.recommendations import generate_executive_recommendations

__all__ = [
    "get_executive_intelligence",
    "generate_business_insights",
    "generate_executive_recommendations",
]
