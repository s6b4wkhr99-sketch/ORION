"""ORION Commercial Intelligence — batch recalculation for existing customer DB."""

from __future__ import annotations

import logging
import uuid
from typing import Callable

from sqlalchemy.orm import Session, joinedload

from app.acquisition.rollup import build_upload_rollup
from app.acquisition.upload import _get_zip_ref
from app.cache.dashboard_cache import invalidate_dashboard_cache
from app.commercial.engine import run_commercial_post_engine, run_commercial_pre_engine
from app.intelligence.forecasting import run_forecast_engine
from app.intelligence.pipeline import run_intelligence_pipeline
from app.intelligence.recommendation import run_recommendation_engine
from app.intelligence.trace_storage import BATCH_COMMIT_ROWS, BATCH_FLUSH_ROWS, persist_intelligence_result
from app.intelligence.types import IntelligenceContext
from app.intelligence.zip_engine import run_zip_intelligence_engine
from app.models.customer import Customer, CustomerDatalogix, CustomerIntelligence
from app.reference.registry import COMMERCIAL_VERSION

logger = logging.getLogger("cios.commercial")

GENERATED_BY = f"commercial_recalc:{COMMERCIAL_VERSION}"


def _index_category(value: float | None) -> str:
    if value is None:
        return "Low"
    if value >= 0.75:
        return "High"
    if value >= 0.45:
        return "Medium"
    return "Low"


def _datalogix_from_profile(profile: CustomerDatalogix | None) -> dict:
    if profile is None:
        return {}
    return {
        "age_range": profile.age_range,
        "generation": profile.generation,
        "gender": profile.gender,
        "estimated_income": profile.estimated_income,
        "home_value": profile.home_value,
        "household": profile.household,
        "length_of_residence": profile.length_of_residence,
        "net_worth": profile.net_worth,
        "online_access": profile.online_access,
        "retail_card": profile.retail_card,
        "dwelling": profile.dwelling,
        "bank_card": profile.bank_card,
        "adults": profile.adults,
        "children": profile.children,
        "persons": profile.persons,
        "dma_code": profile.dma_code,
        "county_code": profile.county_code,
    }


def _context_from_existing(
    customer: Customer,
    intel: CustomerIntelligence,
    datalogix: dict,
    zip_ref: dict | None,
    zip_lookup: Callable[[str], dict | None] | None,
) -> IntelligenceContext:
    ctx = IntelligenceContext(
        customer={
            "email": customer.email,
            "state": customer.state,
            "zip": customer.zip,
            "city": customer.city,
        },
        datalogix_raw=datalogix,
        zip_ref=zip_ref,
    )
    ctx.purchase_power_index = float(intel.purchase_power_index or 0)
    ctx.pain_index = float(intel.pain_index or 0)
    ctx.lifestyle_index = float(intel.lifestyle_index or 0)
    ctx.email_response_index = float(intel.email_response_index or 0)
    ctx.brand_familiarity_index = float(intel.brand_familiarity_index or 0)
    ctx.purchase_power_category = _index_category(intel.purchase_power_index)
    ctx.pain_index_category = _index_category(intel.pain_index)
    ctx.lifestyle_category = _index_category(intel.lifestyle_index)
    ctx.campaign_priority = float(intel.campaign_priority or 0)
    ctx.campaign_priority_category = _index_category(intel.campaign_priority)
    run_zip_intelligence_engine(ctx, zip_lookup=zip_lookup)
    return ctx


def _recalculate_customer(
    customer: Customer,
    intel: CustomerIntelligence,
    *,
    full_pipeline: bool,
    zip_lookup: Callable[[str], dict | None] | None,
) -> dict:
    datalogix = _datalogix_from_profile(customer.datalogix)
    zip_ref = _get_zip_ref_from_lookup(customer.zip, zip_lookup)

    if full_pipeline:
        pipeline = run_intelligence_pipeline(
            customer={
                "email": customer.email,
                "state": customer.state,
                "zip": customer.zip,
                "city": customer.city,
            },
            datalogix_raw=datalogix,
            zip_lookup=zip_lookup,
            zip_ref=zip_ref,
        )
        result = pipeline.to_intelligence_dict()
        result["generated_by"] = GENERATED_BY
        return result

    ctx = _context_from_existing(customer, intel, datalogix, zip_ref, zip_lookup)
    from app.intelligence.datalogix_engine import run_datalogix_engine
    from app.intelligence.geo_intelligence import apply_geo_market_intelligence
    from app.intelligence.lifestyle import run_lifestyle_engine
    from app.intelligence.pain_index import run_pain_index_engine
    from app.intelligence.purchase_power import run_purchase_power_engine
    from app.intelligence.ceragem import run_ceragem_segment_engine
    from app.intelligence.prizm import run_prizm_proxy_engine
    from app.commercial.engine import apply_zip_income_proxy

    run_datalogix_engine(ctx)
    apply_geo_market_intelligence(ctx)
    apply_zip_income_proxy(ctx)
    ctx.prizm_proxy_segment = run_prizm_proxy_engine(ctx)
    run_purchase_power_engine(ctx)
    run_pain_index_engine(ctx)
    run_lifestyle_engine(ctx)
    from app.intelligence.sleep_segmentation import apply_sleep_segment_intelligence

    apply_sleep_segment_intelligence(ctx)
    ctx.ceragem_segment = run_ceragem_segment_engine(ctx)
    from app.intelligence.calculation_framework import apply_calculation_framework
    from app.intelligence.message_direction import run_message_direction_engine

    ctx.message_direction = run_message_direction_engine(ctx)
    run_commercial_pre_engine(ctx)
    run_recommendation_engine(ctx)
    run_commercial_post_engine(ctx)
    run_forecast_engine(ctx)
    apply_calculation_framework(ctx)
    result = ctx.to_intelligence_dict()
    result["generated_by"] = GENERATED_BY
    return result


def _get_zip_ref_from_lookup(zip_code: str | None, zip_lookup: Callable[[str], dict | None] | None) -> dict | None:
    if not zip_code or zip_lookup is None:
        return None
    return zip_lookup(zip_code)


def count_customers(db: Session, upload_id: uuid.UUID | None = None) -> int:
    q = db.query(Customer.customer_id)
    if upload_id:
        q = q.filter(Customer.upload_id == upload_id)
    return q.count()


def recalculate_commercial_intelligence(
    db: Session,
    *,
    upload_id: uuid.UUID | None = None,
    batch_size: int = 2000,
    commit_every: int = 5000,
    full_pipeline: bool = False,
    store_full_trace: bool = False,
    record_versions: bool = False,
    sync_recommendation: bool = False,
    progress_every: int = 10000,
) -> dict[str, int | str]:
    """
    Re-run commercial recommendation + forecast for all customers (default fast path).
    Rebuilds upload rollups and clears dashboard cache when complete.

    Bulk recalc defaults skip version history and per-row AI recommendation sync
    to avoid multi-GB bloat and ~40% slower throughput.
    """
    stats: dict[str, int | str] = {
        "commercial_version": COMMERCIAL_VERSION,
        "processed": 0,
        "errors": 0,
        "uploads_rebuilt": 0,
        "mode": "full_pipeline" if full_pipeline else "commercial_fast",
        "layers": "prizm+pp+pain+lifestyle+ceragem_5tier+baseline_uplift",
    }

    def zip_lookup(z: str) -> dict | None:
        return _get_zip_ref(db, z)

    rows_since_flush = 0
    rows_since_commit = 0
    upload_ids: set[uuid.UUID] = set()
    last_customer_id: uuid.UUID | None = None

    while True:
        batch_query = (
            db.query(Customer)
            .options(joinedload(Customer.datalogix), joinedload(Customer.intelligence))
            .order_by(Customer.customer_id)
        )
        if upload_id:
            batch_query = batch_query.filter(Customer.upload_id == upload_id)
        if last_customer_id is not None:
            batch_query = batch_query.filter(Customer.customer_id > last_customer_id)
        batch = batch_query.limit(batch_size).all()
        if not batch:
            break

        for customer in batch:
            intel = customer.intelligence
            if intel is None:
                stats["errors"] = int(stats["errors"]) + 1
                continue
            try:
                result = _recalculate_customer(
                    customer,
                    intel,
                    full_pipeline=full_pipeline,
                    zip_lookup=zip_lookup,
                )
                persist_intelligence_result(
                    db,
                    customer,
                    result,
                    store_full_trace=store_full_trace,
                    record_versions=record_versions,
                    sync_recommendation=sync_recommendation,
                    generated_by=GENERATED_BY,
                )
                upload_ids.add(customer.upload_id)
                stats["processed"] = int(stats["processed"]) + 1
                rows_since_flush += 1
                rows_since_commit += 1

                if rows_since_flush >= BATCH_FLUSH_ROWS:
                    db.flush()
                    rows_since_flush = 0
                if rows_since_commit >= commit_every:
                    db.commit()
                    rows_since_commit = 0
                processed = int(stats["processed"])
                if progress_every and processed % progress_every == 0:
                    logger.info("Commercial recalc progress: %s customers", processed)
            except Exception:
                logger.exception("Commercial recalc failed for customer %s", customer.customer_id)
                stats["errors"] = int(stats["errors"]) + 1

        last_customer_id = batch[-1].customer_id
        db.commit()
        rows_since_commit = 0
        rows_since_flush = 0

    db.commit()

    for uid in upload_ids:
        build_upload_rollup(db, uid)
        stats["uploads_rebuilt"] = int(stats["uploads_rebuilt"]) + 1
    db.commit()

    invalidate_dashboard_cache()
    logger.info("Commercial recalc complete: %s", stats)
    return stats
