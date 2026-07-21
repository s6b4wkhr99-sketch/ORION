"""Saved Opportunity Finder audience recommendations for Administration > Audience Export."""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import uuid
from collections.abc import Iterable, Iterator
from datetime import datetime

from sqlalchemy.orm import Session

from app.campaign.opportunity_simulate import (
    _apply_segment_filters,
    _apply_skus,
    _apply_states,
    _base_query,
)
from app.config import settings
from app.models.export import AudienceExportRecommendation
from app.models.customer import Customer, CustomerIntelligence
from app.providers.export_builder import get_export_headers, resolve_export_value
from app.utils.timezone import now_app

EXPORT_BATCH_SIZE = 5000
logger = logging.getLogger(__name__)


def _serialize_skus(main_sku: str, additional_skus: list[str] | None) -> list[str]:
    skus = [main_sku.strip()] if main_sku else []
    for sku in additional_skus or []:
        code = (sku or "").strip()
        if code and code not in skus:
            skus.append(code)
    return skus


def _default_name(main_sku: str, geo_scope: str) -> str:
    stamp = now_app().strftime("%b %d, %Y %H:%M")
    scope = geo_scope if geo_scope and geo_scope != "National" else "National"
    if len(scope) > 48:
        scope = f"{scope[:45]}..."
    return f"Opportunity · {main_sku} · {scope} · {stamp}"


def _audience_query(db: Session, rec: AudienceExportRecommendation):
    skus = json.loads(rec.additional_skus_json or "[]")
    if rec.main_sku and rec.main_sku not in skus:
        skus = [rec.main_sku, *skus]
    states = json.loads(rec.states_json or "[]")
    segment_filters = json.loads(rec.segment_filters_json) if rec.segment_filters_json else None
    upload_id = str(rec.upload_id) if rec.upload_id else None

    q = _base_query(db, upload_id)
    q = _apply_skus(q, skus)
    q = _apply_states(q, states or None)
    q = _apply_segment_filters(q, segment_filters)
    return q


def _row_payload(rec: AudienceExportRecommendation) -> dict:
    return {
        "id": str(rec.recommendation_id),
        "name": rec.name,
        "mainSku": rec.main_sku,
        "additionalSkus": json.loads(rec.additional_skus_json or "[]"),
        "states": json.loads(rec.states_json or "[]"),
        "segmentFilters": json.loads(rec.segment_filters_json) if rec.segment_filters_json else None,
        "uploadId": str(rec.upload_id) if rec.upload_id else None,
        "forecastCustomers": rec.forecast_customers,
        "forecastRevenue": rec.forecast_revenue,
        "predictedConversion": rec.predicted_conversion,
        "expectedOrders": rec.expected_orders,
        "geoScope": rec.geo_scope,
        "createdAt": rec.created_at.isoformat() if rec.created_at else None,
        "createdBy": rec.created_by,
        "downloadUrl": f"/api/v1/audience-exports/{rec.recommendation_id}/download",
    }


def create_audience_export(
    db: Session,
    *,
    main_sku: str,
    additional_skus: list[str] | None,
    states: list[str] | None,
    segment_filters: dict | None,
    upload_id: str | None,
    forecast_customers: int,
    forecast_revenue: float,
    predicted_conversion: float,
    expected_orders: float,
    geo_scope: str,
    name: str | None = None,
    created_by: str | None = None,
) -> dict:
    if not main_sku or not main_sku.strip():
        raise ValueError("main_sku is required")

    skus = _serialize_skus(main_sku, additional_skus)
    state_list = [s.strip().upper() for s in (states or []) if s and s.strip()]
    geo = geo_scope.strip() if geo_scope and geo_scope.strip() else ("National" if not state_list else ", ".join(state_list))
    uid = uuid.UUID(upload_id) if upload_id else None

    rec = AudienceExportRecommendation(
        name=(name or _default_name(main_sku.strip(), geo)).strip(),
        main_sku=main_sku.strip(),
        additional_skus_json=json.dumps([sku for sku in skus if sku != main_sku.strip()]),
        states_json=json.dumps(state_list),
        segment_filters_json=json.dumps(segment_filters) if segment_filters else None,
        upload_id=uid,
        forecast_customers=int(forecast_customers or 0),
        forecast_revenue=round(float(forecast_revenue or 0), 2),
        predicted_conversion=round(float(predicted_conversion or 0), 6),
        expected_orders=round(float(expected_orders or 0), 2),
        geo_scope=geo,
        created_by=created_by,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return _row_payload(rec)


def list_audience_exports(db: Session, *, limit: int = 100) -> list[dict]:
    rows = (
        db.query(AudienceExportRecommendation)
        .order_by(AudienceExportRecommendation.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_row_payload(row) for row in rows]


def delete_audience_export(db: Session, recommendation_id: str) -> bool:
    try:
        rid = uuid.UUID(recommendation_id)
    except ValueError:
        return False
    row = db.query(AudienceExportRecommendation).filter(AudienceExportRecommendation.recommendation_id == rid).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def get_audience_export(db: Session, recommendation_id: str) -> AudienceExportRecommendation | None:
    try:
        rid = uuid.UUID(recommendation_id)
    except ValueError:
        return None
    return db.query(AudienceExportRecommendation).filter(AudienceExportRecommendation.recommendation_id == rid).first()


def audience_export_file_name(rec: AudienceExportRecommendation) -> str:
    return f"audience_export_{rec.recommendation_id.hex[:8]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"


def _build_export_row(
    headers: list[tuple[str, str]],
    *,
    campaign_id: str,
    campaign_name: str,
    customer: Customer,
    intel: CustomerIntelligence,
) -> dict[str, str]:
    row_values: dict[str, str] = {}
    for field, label in headers:
        if field == "campaign_id":
            row_values[label] = campaign_id
        elif field == "campaign_name":
            row_values[label] = campaign_name
        elif field == "ceragem_segment":
            row_values[label] = intel.ceragem_segment or intel.prizm_proxy_segment or ""
        elif field.startswith("intel_"):
            row_values[label] = ""
        else:
            row_values[label] = resolve_export_value(field, customer, intel)
    return row_values


def _iter_audience_csv_rows(db: Session, rec: AudienceExportRecommendation) -> Iterator[str]:
    headers = get_export_headers(db, "Generic CSV")
    fieldnames = [label for _, label in headers]
    campaign_name = rec.name
    campaign_id = f"AUD-{rec.recommendation_id.hex[:8].upper()}"

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    yield buffer.getvalue()

    q = _audience_query(db, rec).order_by(Customer.customer_id)
    last_customer_id = None

    while True:
        page = q
        if last_customer_id is not None:
            page = page.filter(Customer.customer_id > last_customer_id)
        batch = page.limit(EXPORT_BATCH_SIZE).all()
        if not batch:
            break

        buffer.seek(0)
        buffer.truncate(0)
        for customer, intel in batch:
            last_customer_id = customer.customer_id
            writer.writerow(
                _build_export_row(
                    headers,
                    campaign_id=campaign_id,
                    campaign_name=campaign_name,
                    customer=customer,
                    intel=intel,
                )
            )
        yield buffer.getvalue()


def stream_audience_csv(recommendation_id: str) -> tuple[str, Iterable[bytes]]:
    """Stream CSV bytes using a dedicated DB session (safe for long-running downloads)."""
    from app.database import SessionLocal

    session = SessionLocal()
    rec = get_audience_export(session, recommendation_id)
    if not rec:
        session.close()
        raise ValueError("Audience export recommendation not found")

    file_name = audience_export_file_name(rec)
    logger.info(
        "Audience export stream started id=%s upload_id=%s forecast_customers=%s",
        recommendation_id,
        rec.upload_id,
        rec.forecast_customers,
    )

    def iter_bytes() -> Iterator[bytes]:
        row_count = 0
        try:
            for chunk in _iter_audience_csv_rows(session, rec):
                if row_count == 0:
                    row_count += 1
                    yield chunk.encode("utf-8")
                    continue
                batch_rows = max(0, chunk.count("\n"))
                row_count += batch_rows
                yield chunk.encode("utf-8")
            logger.info("Audience export stream completed id=%s rows=%s", recommendation_id, max(0, row_count - 1))
        finally:
            session.close()

    return file_name, iter_bytes()


def export_audience_csv(db: Session, recommendation_id: str) -> tuple[str, str, int]:
    rec = get_audience_export(db, recommendation_id)
    if not rec:
        raise ValueError("Audience export recommendation not found")

    os.makedirs(settings.upload_dir, exist_ok=True)
    file_name = audience_export_file_name(rec)
    file_path = os.path.join(settings.upload_dir, file_name)
    customer_count = 0

    with open(file_path, "w", encoding="utf-8", newline="") as handle:
        for chunk in _iter_audience_csv_rows(db, rec):
            handle.write(chunk)
            if customer_count == 0:
                customer_count = 1
                continue
            customer_count += max(0, chunk.count("\n"))

    return file_path, file_name, max(0, customer_count - 1)
