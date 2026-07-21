"""Email campaign opportunity simulator — multi-SKU, multi-state, multi-segment."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from app.campaign.opportunity_simulate import simulate_email_campaign_opportunity
from app.database import SessionLocal
from app.models.customer import Customer, CustomerIntelligence
from app.models.raw import RawUpload


@pytest.fixture
def db():
    session = SessionLocal()
    created_upload_ids: list[uuid.UUID] = []
    try:
        yield session, created_upload_ids
        session.rollback()
    finally:
        if created_upload_ids:
            session.query(CustomerIntelligence).filter(
                CustomerIntelligence.customer_id.in_(
                    session.query(Customer.customer_id).filter(Customer.upload_id.in_(created_upload_ids))
                )
            ).delete(synchronize_session=False)
            session.query(Customer).filter(Customer.upload_id.in_(created_upload_ids)).delete(synchronize_session=False)
            session.query(RawUpload).filter(RawUpload.upload_id.in_(created_upload_ids)).delete(synchronize_session=False)
            session.commit()
        session.close()


@pytest.fixture(autouse=True)
def mock_metro_dashboard():
    with patch(
        "app.campaign.dashboards.get_metro_intelligence_dashboard",
        return_value={"metros": []},
    ):
        yield


def _seed_bundle(db, created_upload_ids: list[uuid.UUID]):
    upload = RawUpload(
        upload_id=uuid.uuid4(),
        filename="test.csv",
        status="completed",
    )
    db.add(upload)
    db.flush()
    created_upload_ids.append(upload.upload_id)
    return upload


def _seed_customer(
    db,
    upload: RawUpload,
    *,
    state: str,
    product: str,
    ceragem: str,
    prizm: str,
    lifestyle: float,
    pain: float,
    brand: float,
    purchase_power: float | None = None,
):
    customer = Customer(
        customer_id=uuid.uuid4(),
        upload_id=upload.upload_id,
        email=f"{state.lower()}-{product.replace(' ', '')}-{uuid.uuid4().hex[:6]}@test.com",
        state=state,
        zip="06801",
    )
    db.add(customer)
    db.flush()
    db.add(
        CustomerIntelligence(
            customer_id=customer.customer_id,
            recommended_product=product,
            expected_revenue=1000.0,
            expected_conversion=0.25,
            ceragem_segment=ceragem,
            prizm_proxy_segment=prizm,
            lifestyle_index=lifestyle,
            pain_index=pain,
            brand_familiarity_index=brand,
            purchase_power_index=purchase_power,
        )
    )
    db.commit()


def test_simulate_requires_main_sku(db):
    session, _ = db
    with pytest.raises(ValueError, match="main_sku"):
        simulate_email_campaign_opportunity(session, None, main_sku="")


def test_simulate_multi_sku_and_state_filters(db):
    session, created = db
    upload = _seed_bundle(session, created)
    _seed_customer(session, upload, state="CA", product="Master V6", ceragem="Mid-High+ · Wellness", prizm="Affluent", lifestyle=0.8, pain=0.7, brand=0.6)
    _seed_customer(session, upload, state="TX", product="Master V6", ceragem="Mid-Low+ · Pain Index", prizm="Suburban", lifestyle=0.5, pain=0.8, brand=0.4)
    _seed_customer(session, upload, state="CA", product="Pause M10", ceragem="Mid-High+ · Wellness", prizm="Affluent", lifestyle=0.75, pain=0.6, brand=0.55)

    result = simulate_email_campaign_opportunity(
        session,
        str(upload.upload_id),
        main_sku="Master V6",
        additional_skus=["Pause M10"],
        states=["CA"],
    )

    assert result["main_sku"] == "Master V6"
    assert set(result["skus"]) == {"Master V6", "Pause M10"}
    assert result["db_potential"]["customers"] == 3
    assert result["phase1"]["kpis"]["customers"] == 2
    assert all(row["state"] == "CA" for row in result["phase1"]["by_state"])


def test_simulate_segment_filters_refine_phase2(db):
    session, created = db
    upload = _seed_bundle(session, created)
    _seed_customer(
        session,
        upload,
        state="NY",
        product="Master V6",
        ceragem="Mid-High+ · Wellness",
        prizm="Urban",
        lifestyle=0.8,
        pain=0.7,
        brand=0.6,
        purchase_power=0.8,
    )
    _seed_customer(
        session,
        upload,
        state="NY",
        product="Master V6",
        ceragem="Mid-Low+ · Pain Index",
        prizm="Urban",
        lifestyle=0.5,
        pain=0.8,
        brand=0.4,
        purchase_power=0.3,
    )

    result = simulate_email_campaign_opportunity(
        session,
        str(upload.upload_id),
        main_sku="Master V6",
        states=["NY"],
        segment_filters={"ceragem": ["Mid-High"]},
    )

    assert result["phase1"]["kpis"]["customers"] == 2
    assert result["phase2"]["kpis"]["customers"] == 1
    assert "Mid-High" in result["phase2"]["segment_distributions"]["ceragem"]
    assert result["phase2"]["segment_distributions"]["ceragem"]["Mid-Low"] == 1


def test_simulate_prizm_unclassified_is_merged(db):
    session, created = db
    upload = _seed_bundle(session, created)
    _seed_customer(
        session,
        upload,
        state="NY",
        product="Master V6",
        ceragem="Mid-High+ · Wellness",
        prizm="Unknown",
        lifestyle=0.8,
        pain=0.7,
        brand=0.6,
    )
    _seed_customer(
        session,
        upload,
        state="NY",
        product="Master V6",
        ceragem="Mid-Low+ · Pain Index",
        prizm="B",
        lifestyle=0.5,
        pain=0.8,
        brand=0.4,
    )

    result = simulate_email_campaign_opportunity(
        session,
        str(upload.upload_id),
        main_sku="Master V6",
        states=["NY"],
    )

    prizm = result["phase2"]["segment_distributions"]["prizm"]
    assert set(prizm.keys()) == {"Unclassified"}
    assert prizm["Unclassified"] == 2

    filtered = simulate_email_campaign_opportunity(
        session,
        str(upload.upload_id),
        main_sku="Master V6",
        states=["NY"],
        segment_filters={"prizm": ["Unclassified"]},
    )
    assert filtered["phase2"]["kpis"]["customers"] == 2


def test_simulate_purchase_power_segment_filter(db):
    session, created = db
    upload = _seed_bundle(session, created)
    _seed_customer(
        session,
        upload,
        state="NY",
        product="Master V6",
        ceragem="Mid-High+ · Wellness",
        prizm="Urban",
        lifestyle=0.8,
        pain=0.7,
        brand=0.6,
        purchase_power=0.8,
    )
    _seed_customer(
        session,
        upload,
        state="NY",
        product="Master V6",
        ceragem="Mid-Low+ · Pain Index",
        prizm="Urban",
        lifestyle=0.5,
        pain=0.8,
        brand=0.4,
        purchase_power=0.3,
    )

    result = simulate_email_campaign_opportunity(
        session,
        str(upload.upload_id),
        main_sku="Master V6",
        states=["NY"],
        segment_filters={"purchase_power": ["High"]},
    )

    assert result["phase1"]["kpis"]["customers"] == 2
    assert result["phase2"]["kpis"]["customers"] == 1
    assert "High" in result["phase2"]["segment_distributions"]["purchase_power"]
    assert result["phase2"]["segment_distributions"]["purchase_power"]["Low"] == 1
