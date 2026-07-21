"""Audience export recommendation persistence."""

from __future__ import annotations

import uuid

import pytest

from app.campaign.audience_export import create_audience_export, delete_audience_export, list_audience_exports
from app.database import SessionLocal
from app.models.export import AudienceExportRecommendation
from app.models.raw import RawUpload


@pytest.fixture
def db():
    session = SessionLocal()
    created_ids: list[uuid.UUID] = []
    try:
        yield session, created_ids
        session.rollback()
    finally:
        if created_ids:
            session.query(AudienceExportRecommendation).filter(
                AudienceExportRecommendation.recommendation_id.in_(created_ids)
            ).delete(synchronize_session=False)
            session.query(RawUpload).filter(RawUpload.upload_id.in_(created_ids)).delete(synchronize_session=False)
            session.commit()
        session.close()


def test_create_list_and_delete_audience_export(db):
    session, created = db
    upload = RawUpload(upload_id=uuid.uuid4(), filename="test.csv", status="completed")
    session.add(upload)
    session.commit()
    created.append(upload.upload_id)

    row = create_audience_export(
        session,
        main_sku="Master V6",
        additional_skus=["Pause M10"],
        states=["CA", "NY"],
        segment_filters={"prizm": ["Wellness Seekers"]},
        upload_id=str(upload.upload_id),
        forecast_customers=1200,
        forecast_revenue=50000.0,
        predicted_conversion=0.0064,
        expected_orders=7.68,
        geo_scope="CA, NY",
        created_by="tester@example.com",
    )
    created.append(uuid.UUID(row["id"]))

    assert row["mainSku"] == "Master V6"
    assert row["forecastCustomers"] == 1200
    assert row["geoScope"] == "CA, NY"

    items = list_audience_exports(session)
    assert any(item["id"] == row["id"] for item in items)

    assert delete_audience_export(session, row["id"]) is True
    assert delete_audience_export(session, row["id"]) is False
