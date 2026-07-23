"""Persist Commercial Simulator campaign forecasts for actual-vs-plan comparison."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.commercial import CommercialSimulatorForecast
from app.utils.timezone import now_app


def _default_name(main_sku: str, additional_skus: list[str]) -> str:
    stamp = now_app().strftime("%b %d, %Y %H:%M")
    sku_label = main_sku if not additional_skus else f"{main_sku} + {len(additional_skus)}"
    return f"Campaign Forecast · {sku_label} · {stamp}"


def _row_payload(row: CommercialSimulatorForecast, *, include_details: bool = False) -> dict:
    payload = {
        "id": str(row.forecast_id),
        "name": row.name,
        "mainSku": row.main_sku,
        "additionalSkus": json.loads(row.additional_skus_json or "[]"),
        "targetCustomers": row.target_customers,
        "expectedOrders": row.expected_orders,
        "revenueForecast": row.revenue_forecast,
        "netProfit": row.net_profit,
        "conversionPrediction": row.conversion_prediction,
        "opportunityScore": row.opportunity_score,
        "audienceFileName": row.audience_file_name,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "createdBy": row.created_by,
    }
    if include_details:
        payload["inputs"] = json.loads(row.inputs_json or "{}")
        payload["result"] = json.loads(row.result_json or "{}")
        payload["audience"] = json.loads(row.audience_json) if row.audience_json else None
    return payload


def save_commercial_simulator_forecast(
    db: Session,
    *,
    name: str | None,
    main_sku: str,
    additional_skus: list[str] | None,
    inputs: dict[str, Any],
    result: dict[str, Any],
    audience: dict[str, Any] | None = None,
    audience_file_name: str | None = None,
    created_by: str | None = None,
) -> dict:
    if not main_sku or not main_sku.strip():
        raise ValueError("main_sku is required")
    if not result:
        raise ValueError("Simulation result is required")

    extras = [sku.strip() for sku in (additional_skus or []) if sku and sku.strip()]
    row = CommercialSimulatorForecast(
        name=(name or _default_name(main_sku.strip(), extras)).strip(),
        main_sku=main_sku.strip(),
        additional_skus_json=json.dumps(extras),
        target_customers=int(result.get("target_customers") or inputs.get("targetCustomers") or 0),
        expected_orders=round(float(result.get("expected_orders") or 0), 2),
        revenue_forecast=round(float(result.get("revenue_forecast") or 0), 2),
        net_profit=round(float(result.get("net_profit") or 0), 2),
        conversion_prediction=round(float(result.get("conversion_prediction") or 0), 8),
        opportunity_score=round(float(result.get("opportunity_score") or 0), 1),
        audience_file_name=audience_file_name,
        inputs_json=json.dumps(inputs),
        result_json=json.dumps(result),
        audience_json=json.dumps(audience) if audience else None,
        created_by=created_by,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_payload(row, include_details=True)


def list_commercial_simulator_forecasts(db: Session, *, limit: int = 50) -> list[dict]:
    rows = (
        db.query(CommercialSimulatorForecast)
        .order_by(CommercialSimulatorForecast.created_at.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return [_row_payload(row) for row in rows]


def get_commercial_simulator_forecast(db: Session, forecast_id: str) -> dict | None:
    try:
        fid = uuid.UUID(forecast_id)
    except ValueError:
        return None
    row = db.query(CommercialSimulatorForecast).filter(CommercialSimulatorForecast.forecast_id == fid).first()
    if not row:
        return None
    return _row_payload(row, include_details=True)


def delete_commercial_simulator_forecast(db: Session, forecast_id: str) -> bool:
    try:
        fid = uuid.UUID(forecast_id)
    except ValueError:
        return False
    row = db.query(CommercialSimulatorForecast).filter(CommercialSimulatorForecast.forecast_id == fid).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
