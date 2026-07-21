"""Volume 18 Section 16–17 — Campaign learning integration & feedback weights."""

import json
from collections import Counter

from sqlalchemy.orm import Session

from app.models.learning import CampaignLearning, LearningCampaign


def compute_learning_weights(db: Session) -> dict:
    """Derive recommendation weights from immutable learning records (read-only)."""
    weights = {
        "product": Counter(),
        "message": Counter(),
        "state": Counter(),
        "campaign_type": Counter(),
        "global_boost": 0.0,
    }

    for row in db.query(CampaignLearning).all():
        boost = (row.learning_score or 50) / 100
        weights["global_boost"] = max(weights["global_boost"], boost - 0.5)
        if row.product_distribution:
            try:
                for product, count in json.loads(row.product_distribution).items():
                    weights["product"][product] += count * boost
            except (json.JSONDecodeError, TypeError):
                pass
        if row.message_direction:
            try:
                for msg, count in json.loads(row.message_direction).items():
                    weights["message"][msg] += count * boost
            except (json.JSONDecodeError, TypeError):
                pass

    for insight in db.query(LearningCampaign).all():
        if insight.product:
            weights["product"][insight.product] += (insight.score or 50) / 50
        if insight.state:
            weights["state"][insight.state] += (insight.roi or 0.5)

    return weights


def learning_adjustment_for_product(db: Session, product: str) -> float:
    weights = compute_learning_weights(db)
    if not weights["product"]:
        return weights["global_boost"] * 10
    top = weights["product"].most_common(1)[0][0] if weights["product"] else None
    if product == top:
        return 12.0 + weights["global_boost"] * 8
    if product in dict(weights["product"].most_common(3)):
        return 5.0
    return weights["global_boost"] * 5


def learning_adjustment_for_message(db: Session, message: str) -> float:
    weights = compute_learning_weights(db)
    if message in weights["message"]:
        return min(15.0, weights["message"][message] * 2)
    return weights["global_boost"] * 5


def learning_adjustment_for_state(db: Session, state: str | None) -> float:
    if not state:
        return 0.0
    weights = compute_learning_weights(db)
    return min(12.0, weights["state"].get(state, 0) * 3)
