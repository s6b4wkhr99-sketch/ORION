"""Commercial Simulator forecast persistence."""

from __future__ import annotations

import uuid

import pytest

from app.commercial.forecast_storage import (
    delete_commercial_simulator_forecast,
    get_commercial_simulator_forecast,
    list_commercial_simulator_forecasts,
    save_commercial_simulator_forecast,
)
from app.database import SessionLocal
from app.models.commercial import CommercialSimulatorForecast


@pytest.fixture
def db():
    session = SessionLocal()
    created_ids: list[uuid.UUID] = []
    try:
        yield session, created_ids
        session.rollback()
    finally:
        if created_ids:
            session.query(CommercialSimulatorForecast).filter(
                CommercialSimulatorForecast.forecast_id.in_(created_ids)
            ).delete(synchronize_session=False)
            session.commit()
        session.close()


def test_save_list_get_delete_forecast(db):
    session, created = db
    saved = save_commercial_simulator_forecast(
        session,
        name="July Email Test",
        main_sku="Master V6",
        additional_skus=["Master S4"],
        inputs={
            "mainSku": "Master V6",
            "additionalSkus": ["Master S4"],
            "targetCustomers": 5000,
            "additionalPromotionPct": "0.05",
            "additionalPromotionMax": "200",
            "leFrameRate": "0.15",
            "conversionRate": "0.00025",
            "corporatePriority": 0.5,
            "inventoryUnits": "",
        },
        result={
            "simulation": True,
            "target_customers": 5000,
            "expected_orders": 12.5,
            "revenue_forecast": 90000.0,
            "net_profit": 12000.0,
            "conversion_prediction": 0.0000025,
            "opportunity_score": 42.0,
        },
        audience={"product": "Master V6", "target_customers": 5000},
        audience_file_name="audience.csv",
        created_by="test@ceragem.com",
    )
    created.append(uuid.UUID(saved["id"]))

    items = list_commercial_simulator_forecasts(session)
    assert any(item["id"] == saved["id"] for item in items)

    loaded = get_commercial_simulator_forecast(session, saved["id"])
    assert loaded is not None
    assert loaded["name"] == "July Email Test"
    assert loaded["inputs"]["additionalPromotionMax"] == "200"
    assert loaded["result"]["revenue_forecast"] == 90000.0

    assert delete_commercial_simulator_forecast(session, saved["id"]) is True
    assert get_commercial_simulator_forecast(session, saved["id"]) is None
