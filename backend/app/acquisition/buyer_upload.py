"""Buyer file upload — chair purchase facts + ORION email match + GAP summary."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from collections import Counter

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.acquisition.upload import UploadValidationError, _load_dataframe, _safe_str, resolve_storage_path, save_upload_file
from app.campaign.buyer_gap_service import run_upload_gap_analysis
from app.campaign.buyer_profile_gap import norm_email, parse_legacy_location, parse_us_state
from app.intelligence.buyer_gap_mapping import parse_purchase_token
from app.models.buyer import BuyerPurchase
from app.models.customer import Customer, CustomerIntelligence
from app.models.raw import RawUpload
from app.processing.duplicate import normalize_email_key
from app.utils.timezone import now_app_iso

_LEGACY_STATUS_OK = frozenset({"PAID", "PROCESSING"})
_SHOPIFY_PAID = "paid"

_EMAIL_HEADERS = ("e mail", "email", "e-mail", "customer email")
_PRODUCT_HEADERS = (
    "material name",
    "material",
    "product",
    "lineitem name",
    "lineitem sku",
    "line item name",
    "sku",
)
_LOCATION_HEADERS = ("location", "shipping province", "billing province", "shipping state", "state")
_ADDRESS_HEADERS = ("address", "shipping address", "billing address")
_STATUS_HEADERS = ("status", "financial status")
_PAID_HEADERS = ("paid at", "paid at date")
_ORDER_HEADERS = ("ordre number", "order number", "order id", "order name", "name", "#")


def _header_map(columns: list[str]) -> dict[str, str]:
    normalized = {c: (c or "").strip().lower() for c in columns}
    return normalized


def _pick_column(normalized: dict[str, str], candidates: tuple[str, ...]) -> str | None:
    for raw, low in normalized.items():
        if low in candidates:
            return raw
    for raw, low in normalized.items():
        for cand in candidates:
            if cand in low:
                return raw
    return None


def _sheet_score(columns: list[str]) -> int:
    cols = _header_map(columns)
    values = set(cols.values())
    score = 0
    if any(v in values for v in _EMAIL_HEADERS):
        score += 3
    if any(v in values for v in _PRODUCT_HEADERS):
        score += 3
    if any(v in values for v in _STATUS_HEADERS):
        score += 1
    if any(v in values for v in _LOCATION_HEADERS):
        score += 1
    return score


def _load_buyer_dataframe(file_path: str, file_type: str) -> pd.DataFrame:
    """Load buyer CSV/XLSX; for multi-sheet workbooks, pick the sheet with buyer columns."""
    if file_type == "csv":
        return _load_dataframe(file_path, file_type)

    resolved = resolve_storage_path(file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.isfile(resolved):
        raise UploadValidationError(
            f"Uploaded file not found on server: {resolved}",
            details={"file_path": resolved},
        )

    workbook = pd.ExcelFile(resolved)
    best_sheet = workbook.sheet_names[0]
    best_score = -1
    for sheet in workbook.sheet_names:
        preview = pd.read_excel(workbook, sheet_name=sheet, dtype=str, keep_default_na=False, nrows=5)
        score = _sheet_score(list(preview.columns))
        if score > best_score:
            best_score = score
            best_sheet = sheet

    if best_score < 4:
        raise UploadValidationError(
            "Could not find a buyer data sheet (needs Email + Product/Material columns).",
            details={"sheets": workbook.sheet_names, "selected_sheet": best_sheet},
        )
    return pd.read_excel(workbook, sheet_name=best_sheet, dtype=str, keep_default_na=False)


def _detect_format(df: pd.DataFrame) -> str:
    cols = _header_map(list(df.columns))
    values = set(cols.values())
    if "financial status" in values or "lineitem name" in values:
        return "shopify"
    if "material name" in values or "ordre number" in values:
        return "legacy"
    return "generic"


def _iter_buyer_rows(df: pd.DataFrame) -> list[dict]:
    fmt = _detect_format(df)
    cols = _header_map(list(df.columns))
    email_col = _pick_column(cols, _EMAIL_HEADERS)
    product_col = _pick_column(cols, _PRODUCT_HEADERS)
    loc_col = _pick_column(cols, _LOCATION_HEADERS)
    addr_col = _pick_column(cols, _ADDRESS_HEADERS)
    status_col = _pick_column(cols, _STATUS_HEADERS)
    paid_col = _pick_column(cols, _PAID_HEADERS)
    order_col = _pick_column(cols, _ORDER_HEADERS)

    if not email_col or not product_col:
        raise UploadValidationError(
            "Buyer upload requires Email and Product/Material columns.",
            details={"email_col": email_col, "product_col": product_col},
        )

    rows: list[dict] = []
    for idx, row in df.iterrows():
        row_num = int(idx) + 2
        if status_col:
            status = (_safe_str(row.get(status_col)) or "").lower()
            if fmt == "shopify":
                if status != _SHOPIFY_PAID:
                    continue
            elif (_safe_str(row.get(status_col)) or "").upper() not in _LEGACY_STATUS_OK:
                continue

        email = norm_email(_safe_str(row.get(email_col)))
        product = _safe_str(row.get(product_col)) or ""
        token = parse_purchase_token(product)
        if not email or not token:
            continue

        loc_raw = _safe_str(row.get(loc_col)) if loc_col else None
        addr_raw = _safe_str(row.get(addr_col)) if addr_col else None
        source_channel = "legacy" if fmt == "legacy" else ("shopify" if fmt == "shopify" else "generic")
        if fmt == "legacy":
            state = parse_legacy_location(loc_raw, addr_raw)
        else:
            state = parse_us_state(loc_raw, source=source_channel)
        paid_at = _safe_str(row.get(paid_col)) if paid_col else None
        order_ref = _safe_str(row.get(order_col)) if order_col else None
        era = "post2025" if paid_at and (paid_at.startswith("2025") or paid_at.startswith("2026")) else "pre2025"

        rows.append(
            {
                "row_number": row_num,
                "email": email,
                "product_raw": product,
                "sku_token": token,
                "state": state,
                "source_channel": source_channel,
                "paid_at": paid_at,
                "order_ref": order_ref,
                "era": era,
            }
        )
    return rows


def preview_buyer_upload(db: Session, file_path: str, file_name: str) -> dict:
    file_type = "csv" if file_name.lower().endswith(".csv") else "xlsx"
    df = _load_buyer_dataframe(file_path, file_type)
    try:
        parsed = _iter_buyer_rows(df)
    except UploadValidationError as e:
        return {
            "file_name": file_name,
            "total_rows": len(df),
            "fatal_errors": [str(e)],
            "warnings": [],
            "chair_rows": 0,
            "unique_emails": 0,
            "sku_distribution": {},
            "detected_format": _detect_format(df),
        }

    emails = {r["email"] for r in parsed}
    sku_dist = Counter(r["sku_token"] for r in parsed)
    return {
        "file_name": file_name,
        "total_rows": len(df),
        "fatal_errors": [],
        "warnings": [] if parsed else ["No paid chair rows detected — check Status/Financial Status filters."],
        "chair_rows": len(parsed),
        "unique_emails": len(emails),
        "sku_distribution": dict(sku_dist.most_common()),
        "detected_format": _detect_format(df),
        "sample_headers": list(df.columns)[:20],
    }


def _match_customers(db: Session, emails: list[str]) -> dict[str, uuid.UUID]:
    if not emails:
        return {}
    keys = [normalize_email_key(e) for e in emails if e]
    rows = (
        db.query(Customer.customer_id, Customer.email)
        .filter(func.lower(func.trim(Customer.email)).in_(keys))
        .all()
    )
    return {normalize_email_key(r.email): r.customer_id for r in rows if r.email}


def build_source_row_key(row: dict) -> str:
    """Stable per-purchase key — repeat buyers keep separate rows when order/row differs."""
    parts = [
        normalize_email_key(row.get("email")) or "",
        (row.get("sku_token") or "").upper(),
        (row.get("product_raw") or "").strip(),
        (row.get("state") or "OTHER").upper(),
        (row.get("order_ref") or "").strip(),
        (row.get("paid_at") or "").strip(),
        str(row.get("row_number") or ""),
        (row.get("source_channel") or "").strip(),
    ]
    payload = "\x1f".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_existing_source_row_keys(db: Session, keys: set[str]) -> set[str]:
    if not keys:
        return set()
    rows = db.query(BuyerPurchase.source_row_key).filter(BuyerPurchase.source_row_key.in_(keys)).all()
    return {row[0] for row in rows if row[0]}


def _partition_new_purchases(db: Session, parsed: list[dict]) -> tuple[list[dict], int]:
    """Skip only exact same source purchase rows (re-upload), not repeat buyers."""
    candidate_keys = {build_source_row_key(row) for row in parsed}
    existing = _load_existing_source_row_keys(db, candidate_keys)
    new_rows: list[dict] = []
    seen_in_batch: set[str] = set()
    skipped = 0

    for row in parsed:
        key = build_source_row_key(row)
        row["source_row_key"] = key
        if key in existing or key in seen_in_batch:
            skipped += 1
            continue
        seen_in_batch.add(key)
        new_rows.append(row)

    return new_rows, skipped


def process_buyer_upload(
    db: Session,
    file_path: str,
    file_name: str,
    *,
    uploaded_by: str = "system",
) -> RawUpload:
    file_type = "csv" if file_name.lower().endswith(".csv") else "xlsx"
    df = _load_buyer_dataframe(file_path, file_type)
    parsed = _iter_buyer_rows(df)
    if not parsed:
        raise UploadValidationError("No valid buyer chair rows found in file.")

    # Keep stored sku_token aligned with latest parse_purchase_token rules (e.g. M6(s) → M6S).
    reparse_stats = reparse_buyer_sku_tokens(db)

    new_rows, skipped_duplicates = _partition_new_purchases(db, parsed)
    if not new_rows:
        raise UploadValidationError(
            f"All {len(parsed)} purchase rows already exist — no new records added.",
            details={"skipped_duplicates": skipped_duplicates, "parsed_rows": len(parsed)},
        )

    upload = RawUpload(
        upload_id=uuid.uuid4(),
        filename=file_name,
        uploaded_by=uploaded_by,
        provider="buyer_list",
        dataset_type="buyer",
        status="processing",
        file_path=file_path,
        file_type=file_type,
        summary_json=json.dumps({"total_rows": len(df), "started_at": now_app_iso()}),
    )
    db.add(upload)
    db.flush()

    emails = sorted({r["email"] for r in new_rows})
    email_to_customer = _match_customers(db, emails)

    for row in new_rows:
        key = normalize_email_key(row["email"])
        db.add(
            BuyerPurchase(
                upload_id=upload.upload_id,
                row_number=row["row_number"],
                email=row["email"],
                product_raw=row["product_raw"],
                sku_token=row["sku_token"],
                state=row["state"],
                source_channel=row["source_channel"],
                source_row_key=row["source_row_key"],
                matched_customer_id=email_to_customer.get(key),
            )
        )

    db.commit()
    gap_report = run_upload_gap_analysis(db, upload.upload_id)

    matched_rows = sum(1 for r in new_rows if normalize_email_key(r["email"]) in email_to_customer)
    matched_emails = len({r["email"] for r in new_rows if normalize_email_key(r["email"]) in email_to_customer})

    summary = {
        "dataset_type": "buyer",
        "total_rows": len(df),
        "chair_rows": len(new_rows),
        "parsed_rows": len(parsed),
        "rows_inserted": len(new_rows),
        "skipped_duplicates": skipped_duplicates,
        "sku_tokens_reparsed": reparse_stats.get("updated", 0),
        "unique_emails": len(emails),
        "matched_emails": matched_emails,
        "matched_rows": matched_rows,
        "match_rate_pct": round(100 * matched_emails / max(len(emails), 1), 2),
        "sku_distribution": dict(Counter(r["sku_token"] for r in new_rows).most_common()),
        "state_parsed_other": sum(1 for r in new_rows if r["state"] == "OTHER"),
        "gap_report": gap_report,
        "completed_at": now_app_iso(),
        "rows_processed": len(new_rows),
    }
    upload.status = "completed"
    upload.summary_json = json.dumps(summary)
    db.commit()
    db.refresh(upload)
    return upload


def delete_buyer_upload(db: Session, upload_id: uuid.UUID) -> RawUpload | None:
    """Remove a buyer upload and its purchase rows (prospect uploads unaffected)."""
    upload = db.query(RawUpload).filter(RawUpload.upload_id == upload_id).first()
    if not upload:
        return None
    if upload.dataset_type != "buyer":
        raise UploadValidationError("Only buyer dataset uploads can be deleted here.")
    db.query(BuyerPurchase).filter(BuyerPurchase.upload_id == upload_id).delete(synchronize_session=False)
    db.delete(upload)
    db.commit()
    return upload


def buyer_matched_rows_for_download(db: Session, upload_id: uuid.UUID) -> list[dict]:
    purchases = (
        db.query(BuyerPurchase)
        .filter(BuyerPurchase.upload_id == upload_id, BuyerPurchase.matched_customer_id.isnot(None))
        .order_by(BuyerPurchase.row_number)
        .all()
    )
    if not purchases:
        return []

    customer_ids = [p.matched_customer_id for p in purchases if p.matched_customer_id]
    intel_rows = (
        db.query(CustomerIntelligence, Customer)
        .join(Customer, Customer.customer_id == CustomerIntelligence.customer_id)
        .filter(Customer.customer_id.in_(customer_ids))
        .all()
    )
    intel_by_customer = {c.customer_id: (ci, c) for ci, c in intel_rows}
    customer_only = {
        c.customer_id: c
        for c in db.query(Customer).filter(Customer.customer_id.in_(customer_ids)).all()
    }

    from app.intelligence.buyer_gap_mapping import buyer_compare_sku, index_level
    from app.intelligence.product_ladders import resolve_active_ladder

    out: list[dict] = []
    for p in purchases:
        ci, c = intel_by_customer.get(p.matched_customer_id, (None, None))
        if not c:
            c = customer_only.get(p.matched_customer_id)
        if not ci:
            out.append(
                {
                    "email": p.email,
                    "purchased_sku": p.sku_token,
                    "product_raw": p.product_raw,
                    "compare_sku": p.sku_token,
                    "mapping_rule": "no_intelligence",
                    "recommended_product": "",
                    "exact_hit": False,
                    "ceragem_segment": "",
                    "prizm_proxy_segment": "",
                    "purchase_power_index": "",
                    "lifestyle_index": "",
                    "buyer_state": p.state,
                    "prospect_state": c.state if c else "",
                    "ladder_source": "",
                    "ladder": "",
                }
            )
            continue
        compare_sku, mapping_rule = buyer_compare_sku(
            p.product_raw,
            ceragem_segment=ci.ceragem_segment,
            prizm_proxy_segment=ci.prizm_proxy_segment,
            purchase_power_index=ci.purchase_power_index,
            lifestyle_index=ci.lifestyle_index,
            pain_index=ci.pain_index,
            customer_state=c.state,
        )
        pain_cat = index_level(ci.pain_index)
        ladder, ladder_source = resolve_active_ladder(
            ceragem_segment=ci.ceragem_segment,
            prizm_segment=ci.prizm_proxy_segment,
            pain_index_category=pain_cat,
        )
        out.append(
            {
                "email": p.email,
                "purchased_sku": p.sku_token,
                "product_raw": p.product_raw,
                "compare_sku": compare_sku,
                "mapping_rule": mapping_rule,
                "recommended_product": ci.recommended_product,
                "exact_hit": compare_sku == ci.recommended_product,
                "ceragem_segment": ci.ceragem_segment,
                "prizm_proxy_segment": ci.prizm_proxy_segment,
                "purchase_power_index": ci.purchase_power_index,
                "lifestyle_index": ci.lifestyle_index,
                "buyer_state": p.state,
                "prospect_state": c.state,
                "ladder_source": ladder_source,
                "ladder": "|".join(ladder),
            }
        )
    return out


def reparse_buyer_sku_tokens(db: Session) -> dict[str, int]:
    """Re-derive sku_token from product_raw after parse_purchase_token rule changes."""
    rows = db.query(BuyerPurchase).all()
    updated = 0
    for row in rows:
        token = parse_purchase_token(row.product_raw)
        if not token:
            continue
        if token != (row.sku_token or "").upper():
            row.sku_token = token
            updated += 1
    if updated:
        db.commit()
    return {"total": len(rows), "updated": updated}
