"""Volume 15 Section 6 — Import engine orchestration."""

import json
import time
import uuid

import pandas as pd
from sqlalchemy.orm import Session

from app.learning.campaign_learning import create_learning_records_for_report
from app.learning.store import generate_learning_records
from app.models.campaign import Campaign, CampaignProduct, CampaignReportUpload, CampaignState
from app.providers.audit import log_provider_audit
from app.providers.base import ImportContext
from app.providers.import_validation import ImportValidationError
from app.providers.registry import detect_provider_from_headers, get_adapter


def _safe_str(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def _load_dataframe(file_path: str, file_name: str) -> pd.DataFrame:
    if file_name.lower().endswith(".csv"):
        return pd.read_csv(file_path, dtype=str, keep_default_na=False)
    return pd.read_excel(file_path, dtype=str, keep_default_na=False)


def _safe_float(value) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        text = str(value).replace(",", "").replace("%", "").replace("$", "")
        return float(text)
    except ValueError:
        return None


def run_provider_import(
    db: Session,
    file_path: str,
    file_name: str,
    *,
    provider_name: str | None = None,
    user_id: str | None = None,
    role: str | None = None,
) -> CampaignReportUpload:
    started = time.perf_counter()
    df = _load_dataframe(file_path, file_name)
    df.columns = [str(c).strip() for c in df.columns]
    headers = list(df.columns)

    detected = provider_name or detect_provider_from_headers(headers)
    adapter = get_adapter(detected)
    column_map = adapter.build_import_column_map(headers)

    ctx = ImportContext(
        provider_name=detected,
        file_name=file_name,
        file_path=file_path,
        dataframe=df,
        column_map=column_map,
        user_id=user_id,
    )
    validation = adapter.validate_import(ctx)
    if not validation.is_valid:
        raise ImportValidationError(validation.errors)

    report = CampaignReportUpload(filename=file_name, file_path=file_path, status="processing")
    db.add(report)
    db.flush()

    campaigns_seen: dict[str, Campaign] = {}
    state_rows: list[CampaignState] = []
    product_rows: list[CampaignProduct] = []

    for _, row in df.iterrows():
        metrics = adapter.normalize_metrics(row, column_map)
        campaign_id = _safe_str(row.get(column_map.get("campaign_id"))) or f"CAMP-{uuid.uuid4().hex[:8].upper()}"
        campaign_name = _safe_str(row.get(column_map.get("campaign_name"))) or file_name
        state = _safe_str(row.get(column_map.get("state")))
        if state:
            state = state.upper()[:2]

        sent = int(metrics.get("total_sent") or 0)
        delivered = int(metrics.get("delivered") or 0)
        if sent == 0 and delivered > 0:
            sent = delivered
        open_count = int(metrics.get("opened") or 0)
        click = int(metrics.get("clicked") or 0)
        unique_click = int(metrics.get("unique_click") or 0)
        cost_col = column_map.get("cost")
        cost = _safe_float(row.get(cost_col)) if cost_col else None
        revenue = metrics.get("actual_revenue")
        if isinstance(revenue, str):
            revenue = _safe_float(revenue)

        open_rate = _safe_float(row.get(column_map.get("open_rate"))) if column_map.get("open_rate") else None
        ctr = _safe_float(row.get(column_map.get("ctr"))) if column_map.get("ctr") else None
        if open_rate and open_rate > 1:
            open_rate /= 100
        if ctr and ctr > 1:
            ctr /= 100
        open_rate = open_rate or _rate(open_count, sent)
        ctr = ctr or _rate(click, sent)
        roi = _safe_float(row.get(column_map.get("roi"))) if column_map.get("roi") else None
        if roi is None and revenue is not None and cost:
            roi = round((float(revenue) - float(cost)) / float(cost), 4)

        if campaign_id not in campaigns_seen:
            existing = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
            if not existing:
                existing = Campaign(
                    campaign_id=campaign_id,
                    campaign_name=campaign_name,
                    campaign_type=_safe_str(row.get(column_map.get("campaign_type"))) or "Email",
                    status="completed",
                    provider=detected,
                    owner="CIOS Admin",
                    forecast_version="Volume 06 v1.0",
                )
                db.add(existing)
            else:
                existing.provider = detected
            campaigns_seen[campaign_id] = existing

        state_rows.append(
            CampaignState(
                campaign_id=campaign_id,
                state=state,
                sent=sent,
                open=open_count,
                click=click,
                unique_click=unique_click,
                revenue=float(revenue) if revenue is not None else None,
                cost=float(cost) if cost is not None else None,
                roi=roi,
                open_rate=open_rate,
                ctr=ctr,
            )
        )

        category = _safe_str(row.get(column_map.get("category")))
        product = _safe_str(row.get(column_map.get("product")))
        if category or product:
            product_rows.append(
                CampaignProduct(
                    campaign_id=campaign_id,
                    category=category,
                    product=product,
                    click=click,
                    revenue=float(revenue) if revenue is not None else None,
                )
            )

    db.add_all(state_rows)
    db.add_all(product_rows)
    db.flush()

    learning_count = generate_learning_records(db, report.id, state_rows, product_rows)
    campaign_learning_count = create_learning_records_for_report(
        db, report.id, campaigns_seen, state_rows, product_rows
    )

    primary_id = next(iter(campaigns_seen)) if campaigns_seen else None
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    report.campaign_id = primary_id
    report.status = "completed"
    report.summary_json = json.dumps(
        {
            "provider": detected,
            "total_rows": len(df),
            "campaigns_imported": len(campaigns_seen),
            "state_rows": len(state_rows),
            "product_rows": len(product_rows),
            "learning_records_created": learning_count,
            "campaign_learning_records_created": campaign_learning_count,
            "column_map": validation.mapped_columns,
            "warnings": validation.warnings,
        }
    )
    db.commit()
    db.refresh(report)

    # Volume 16 — normalized campaign_report + dashboard refresh
    if campaigns_seen and state_rows:
        primary = campaigns_seen.get(primary_id) if primary_id else None
        totals = {
            "total_sent": sum(r.sent for r in state_rows),
            "delivered": sum(r.sent for r in state_rows),
            "opened": sum(r.open for r in state_rows),
            "clicked": sum(r.click for r in state_rows),
            "unique_click": sum(r.unique_click for r in state_rows),
            "revenue": sum(r.revenue or 0 for r in state_rows),
        }
        from app.schema.triggers import record_campaign_report_summary, update_campaign_actuals

        if primary_id and primary:
            update_campaign_actuals(primary, totals["revenue"], None)
        record_campaign_report_summary(
            db,
            campaign_id=primary_id or next(iter(campaigns_seen)),
            provider=detected,
            total_sent=totals["total_sent"],
            delivered=totals["delivered"],
            opened=totals["opened"],
            clicked=totals["clicked"],
            unique_click=totals["unique_click"],
            ctr=_rate(totals["clicked"], totals["total_sent"]),
            ctor=None,
            revenue=totals["revenue"],
            conversion=None,
        )
        db.commit()

    from app.database import engine as db_engine
    from app.schema.apply import refresh_materialized_views

    refresh_materialized_views(db_engine)

    log_provider_audit(
        db,
        action="provider_import",
        provider=detected,
        campaign_id=primary_id,
        import_id=str(report.id),
        user_id=user_id,
        role=role,
        customer_count=len(df),
        status="success",
        duration_ms=duration_ms,
        warnings=validation.warnings,
    )

    from app.utils.audit_log import audit_report_import

    audit_report_import(str(report.id), primary_id, len(df))
    return report
