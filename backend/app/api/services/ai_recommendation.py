"""Volume 18 Section 24 — AI recommendation API services."""

from sqlalchemy.orm import Session

from app.ai_engine.engine import get_ai_recommendation


def get_full_recommendation(db: Session, customer_id: str) -> dict | None:
    return get_ai_recommendation(db, customer_id)


def get_product_recommendation(db: Session, customer_id: str) -> dict | None:
    data = get_ai_recommendation(db, customer_id)
    if not data:
        return None
    return {"customerId": customer_id, **data["product"], "explanation": data["explanation"]}


def get_message_recommendation(db: Session, customer_id: str) -> dict | None:
    data = get_ai_recommendation(db, customer_id)
    if not data:
        return None
    return {"customerId": customer_id, **data["message"], "explanation": data["explanation"]}


def get_campaign_recommendation(db: Session, customer_id: str) -> dict | None:
    data = get_ai_recommendation(db, customer_id)
    if not data:
        return None
    return {"customerId": customer_id, **data["campaign"], "explanation": data["explanation"]}


def get_geographic_recommendation(db: Session, customer_id: str) -> dict | None:
    data = get_ai_recommendation(db, customer_id)
    if not data:
        return None
    return {"customerId": customer_id, **data["geographic"], "explanation": data["explanation"]}


def get_revenue_prediction(db: Session, customer_id: str) -> dict | None:
    data = get_ai_recommendation(db, customer_id)
    if not data:
        return None
    return {"customerId": customer_id, **data["revenue_prediction"]}


def get_conversion_prediction(db: Session, customer_id: str) -> dict | None:
    data = get_ai_recommendation(db, customer_id)
    if not data:
        return None
    return {"customerId": customer_id, **data["conversion_prediction"]}
