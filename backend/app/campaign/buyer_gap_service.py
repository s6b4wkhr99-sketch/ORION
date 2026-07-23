"""Run GAP analysis for an uploaded buyer batch (DB-backed)."""

from __future__ import annotations

import uuid
from collections import Counter

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.campaign.buyer_profile_gap import (
    build_profile_matrix,
    build_prospect_state_gap,
    calibration_backlog,
    compute_reweight_table,
    distribution_gap,
    prospect_token_distribution,
    reweighted_buyer_sku_distribution,
)
from app.intelligence.buyer_gap_mapping import (
    buyer_compare_sku,
    index_level,
    master_series,
    purchase_series,
)
from app.models.buyer import BuyerPurchase
from app.models.customer import Customer, CustomerIntelligence
from app.models.raw import RawUpload
from app.intelligence.product_ladders import resolve_active_ladder


def _purchases_to_profile_rows(db: Session, upload_id: uuid.UUID) -> list[dict]:
    rows = db.query(BuyerPurchase).filter(BuyerPurchase.upload_id == upload_id).all()
    return [
        {
            "email": r.email,
            "sku_token": r.sku_token,
            "state": r.state or "OTHER",
            "source": r.source_channel or "upload",
            "series": purchase_series(r.sku_token),
        }
        for r in rows
        if r.sku_token
    ]


class _RowAdapter:
    """Minimal adapter for build_profile_matrix from DB dict rows."""

    def __init__(self, data: dict):
        self.email = data["email"]
        self.sku_token = data["sku_token"]
        self.state = data["state"]
        self.source = data["source"]
        self.series = data.get("series")
        self.state_tier = _state_tier(data["state"])
        self.era = "upload"
        self.product_raw = data.get("product_raw", "")
        self.row_id = data.get("row_id", data["email"])


def _state_tier(state: str) -> str:
    from app.campaign.buyer_profile_gap import state_tier

    return state_tier(state)


def run_upload_gap_analysis(db: Session, upload_id: uuid.UUID) -> dict:
    upload = db.query(RawUpload).filter(RawUpload.upload_id == upload_id).first()
    if not upload:
        return {"error": "upload_not_found"}

    purchases = db.query(BuyerPurchase).filter(BuyerPurchase.upload_id == upload_id).all()
    if not purchases:
        return {"error": "no_purchases"}

    adapted = [
        _RowAdapter(
            {
                "email": p.email,
                "sku_token": p.sku_token,
                "state": p.state or "OTHER",
                "source": p.source_channel or "upload",
                "series": purchase_series(p.sku_token),
                "product_raw": p.product_raw or "",
                "row_id": str(p.id),
            }
        )
        for p in purchases
        if p.sku_token
    ]

    profile_matrix = build_profile_matrix(adapted)

    buyer_state_counts = Counter(p.state or "OTHER" for p in purchases if p.sku_token)
    prospect_state_rows = (
        db.query(Customer.state, func.count(Customer.customer_id))
        .join(CustomerIntelligence, CustomerIntelligence.customer_id == Customer.customer_id)
        .filter(Customer.state.isnot(None), func.trim(Customer.state) != "")
        .group_by(Customer.state)
        .all()
    )
    prospect_states = Counter({state: count for state, count in prospect_state_rows if state})
    reweight_table = compute_reweight_table(buyer_state_counts, prospect_states)

    reweight_by_state = {
        r["state"]: r["reweight"]
        for r in reweight_table["by_state"]
        if r.get("reweight") is not None
    }

    all_sku = Counter(p.sku_token for p in purchases if p.sku_token)
    n = sum(all_sku.values()) or 1
    raw_buyer_sku_pct = {k: round(100 * all_sku[k] / n, 2) for k in all_sku}

    prospect_rec_rows = (
        db.query(CustomerIntelligence.recommended_product, func.count(CustomerIntelligence.id))
        .filter(CustomerIntelligence.recommended_product.isnot(None))
        .group_by(CustomerIntelligence.recommended_product)
        .all()
    )
    prospect_rec = Counter({sku: count for sku, count in prospect_rec_rows if sku})
    prospect_sku_pct = prospect_token_distribution(dict(prospect_rec))

    class _ReweightRow:
        def __init__(self, purchase: BuyerPurchase):
            self.sku_token = purchase.sku_token
            self.state = purchase.state or "OTHER"

    reweighted_sku_pct = reweighted_buyer_sku_distribution(
        [_ReweightRow(p) for p in purchases if p.sku_token],
        reweight_by_state,
    )

    raw_gap = distribution_gap(raw_buyer_sku_pct, prospect_sku_pct)
    reweighted_gap = distribution_gap(reweighted_sku_pct, prospect_sku_pct)
    backlog = calibration_backlog(raw_gap, reweighted_gap)

    # Intel-matched rule GAP
    matched = [p for p in purchases if p.matched_customer_id]
    intel_hits = 0
    intel_rows = 0
    for p in matched:
        ci = (
            db.query(CustomerIntelligence)
            .filter(CustomerIntelligence.customer_id == p.matched_customer_id)
            .first()
        )
        if not ci:
            continue
        compare, _ = buyer_compare_sku(
            p.product_raw,
            ceragem_segment=ci.ceragem_segment,
            prizm_proxy_segment=ci.prizm_proxy_segment,
            purchase_power_index=ci.purchase_power_index,
            lifestyle_index=ci.lifestyle_index,
            pain_index=ci.pain_index,
        )
        intel_rows += 1
        if compare == ci.recommended_product:
            intel_hits += 1

    unique_emails = len({p.email for p in purchases})
    matched_emails = len({p.email for p in matched})

    return {
        "upload_id": str(upload_id),
        "chair_rows": len(purchases),
        "unique_emails": unique_emails,
        "matched_emails": matched_emails,
        "matched_rows": len(matched),
        "match_rate_pct": round(100 * matched_emails / max(unique_emails, 1), 2),
        "intel_exact_hit_rate_pct": round(100 * intel_hits / max(intel_rows, 1), 2),
        "aggregate_gap": {
            "raw_buyer_sku_pct": raw_buyer_sku_pct,
            "reweighted_buyer_sku_pct": reweighted_sku_pct,
            "prospect_recommended_sku_pct": prospect_sku_pct,
            "raw_distribution_gap": raw_gap,
            "reweighted_distribution_gap": reweighted_gap,
        },
        "calibration_backlog": backlog[:10],
        "reweight_ca_bias_index": reweight_table.get("ca_bias_index"),
        "state_other_rows": sum(1 for p in purchases if (p.state or "OTHER") == "OTHER"),
    }
