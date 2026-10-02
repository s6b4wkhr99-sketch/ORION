"""Product-fit rollup rebuild — Market / Metro read live recommended_product."""

from __future__ import annotations

import json
import uuid

import pytest

from app.acquisition.rollup import rebuild_product_fit_rollups
from app.database import SessionLocal
from app.models.customer import Customer, CustomerIntelligence
from app.models.raw import RawUpload
from app.models.scale import UploadRollup


@pytest.fixture
def db():
    session = SessionLocal()
    created: list[uuid.UUID] = []
    try:
        yield session, created
        session.rollback()
    finally:
        if created:
            session.query(UploadRollup).filter(UploadRollup.upload_id.in_(created)).delete(synchronize_session=False)
            session.query(CustomerIntelligence).filter(
                CustomerIntelligence.customer_id.in_(
                    session.query(Customer.customer_id).filter(Customer.upload_id.in_(created))
                )
            ).delete(synchronize_session=False)
            session.query(Customer).filter(Customer.upload_id.in_(created)).delete(synchronize_session=False)
            session.query(RawUpload).filter(RawUpload.upload_id.in_(created)).delete(synchronize_session=False)
            session.commit()
        session.close()


def test_rebuild_product_fit_rollups_uses_live_v5(db):
    session, created = db
    upload = RawUpload(upload_id=uuid.uuid4(), filename="fit.csv", status="completed")
    session.add(upload)
    session.flush()
    created.append(upload.upload_id)

    customer = Customer(
        customer_id=uuid.uuid4(),
        upload_id=upload.upload_id,
        email="v5-fit@test.com",
        state="CA",
        zip="90001",
        city="Los Angeles",
    )
    session.add(customer)
    session.flush()
    session.add(
        CustomerIntelligence(
            customer_id=customer.customer_id,
            recommended_product="Master V5",
            expected_revenue=500.0,
            expected_conversion=0.1,
            ceragem_segment="Low+ · Pain Index",
            purchase_power_index=0.25,
        )
    )
    session.add(
        UploadRollup(
            upload_id=upload.upload_id,
            dimension="product",
            scope="CA",
            key="Master S4",
            customer_count=1,
            expected_orders=0.1,
            expected_revenue=500.0,
        )
    )
    session.add(
        UploadRollup(
            upload_id=upload.upload_id,
            dimension="zip",
            scope="CA",
            key="90001",
            customer_count=1,
            expected_orders=0.1,
            expected_revenue=500.0,
            payload_json=json.dumps({"recommended_product": "Master S4", "city": "Los Angeles"}),
        )
    )
    session.commit()

    rebuild_product_fit_rollups(session, upload.upload_id)

    products = {
        row.key: row.customer_count
        for row in session.query(UploadRollup).filter(
            UploadRollup.upload_id == upload.upload_id,
            UploadRollup.dimension == "product",
        )
    }
    assert products.get("Master V5") == 1
    assert "Master S4" not in products

    zip_row = (
        session.query(UploadRollup)
        .filter(
            UploadRollup.upload_id == upload.upload_id,
            UploadRollup.dimension == "zip",
            UploadRollup.key == "90001",
        )
        .one()
    )
    payload = json.loads(zip_row.payload_json)
    assert payload["recommended_product"] == "Master V5"
