"""Volume 07 — RESTful API v1."""

import json
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.acquisition.preview import preview_upload
from app.acquisition.upload import UploadValidationError, process_upload, save_upload_file
from app.acquisition.upload_profile import get_upload_processing_profile
from app.acquisition.upload_queue import enqueue_customer_upload, get_upload_status, upload_status_payload
from app.api.auth import login, refresh
from app.api.deps import (
    get_current_user,
    require_campaign,
    require_campaign_approve,
    require_campaign_write,
    require_customer_intelligence,
    require_dashboard,
    require_export,
    require_forecast,
    require_report_import,
    require_rule_library,
    require_settings,
    require_upload,
    require_user_admin,
)
from app.api.responses import ok
from app.config import settings
from app.api.services.campaigns import (
    CampaignImmutableError,
    approve_campaign,
    create_campaign,
    delete_campaign,
    get_campaign_audience,
    get_campaign_forecast,
    list_campaigns,
    update_campaign,
)
from app.security.audit import list_audit_logs, record_audit
from app.security.upload_validation import UploadRuleError, validate_upload_file
from app.schemas.auth import LoginRequest, RefreshRequest
from app.schemas.admin import UserCreateRequest, UserPasswordRequest, UserRoleRequest
from app.schemas.analytics import AnalyticsReportRequest
from app.schemas.campaign import CampaignCreateRequest, CampaignUpdateRequest
from app.schemas.export import ExportRequest
from app.methodology.service import (
    get_methodology_governance,
    get_methodology_layers,
    get_methodology_overview,
    get_methodology_pyramid,
    get_methodology_success_criteria,
)
from app.knowledge.service import (
    get_knowledge_acceptance_criteria,
    get_knowledge_cross_reference,
    get_knowledge_glossary,
    get_knowledge_governance,
    get_knowledge_index,
    get_knowledge_overview,
)
from app.api.services.mapping import (
    list_field_aliases,
    list_field_master,
    mapping_report_from_file,
    mapping_standardize_payload,
    mapping_validate_from_file,
)
from app.api.services.intelligence_framework import (
    get_customer_intelligence_with_framework,
    get_intelligence_framework,
)
from app.conventions.service import get_conventions_overview, verify_convention_compliance
from app.git_workflow.service import get_git_workflow_overview, verify_git_workflow_compliance
from app.design_principles.service import get_design_principles_overview, verify_design_principles_compliance
from app.reference.service import (
    get_audience_segments,
    get_ceragem_segments,
    get_dashboard_config,
    get_geographic_summary,
    get_product_prices,
    get_products,
    get_prizm_segments,
    get_providers,
    get_purchase_power_levels,
    get_reference_catalog,
    get_reference_version,
)
from app.api.services.ai_recommendation import (
    get_campaign_recommendation,
    get_conversion_prediction,
    get_full_recommendation,
    get_geographic_recommendation,
    get_message_recommendation,
    get_product_recommendation,
    get_revenue_prediction,
)
from app.api.services.customers import (
    get_customer_detail,
    get_customer_intelligence,
    get_customer_recommendation,
    list_customers,
)
from app.campaign.analytics import (
    get_campaign_dashboard,
    get_customer_distribution,
    get_customer_table,
    get_executive_summary,
    list_campaign_reports,
    list_uploads,
)
from app.campaign.dashboards import (
    get_export_preview,
    get_product_dashboard,
    get_roi_dashboard,
    get_settings_info,
    get_state_dashboard,
    get_metro_intelligence_dashboard,
    get_zip_dashboard,
)
from app.geo.zcta_choropleth import get_metro_zcta_choropleth, get_state_zcta_choropleth
from app.campaign.export import enqueue_export_job
from app.providers.export_queue import export_status_payload
from app.providers.export_validation import ExportValidationError
from app.providers.import_validation import ImportValidationError
from app.providers.info import get_provider, list_providers
from app.campaign.forecast import compute_campaign_forecast
from app.campaign.reports import process_campaign_report
from app.database import get_db
from app.operations.admin_dashboard import get_admin_dashboard
from app.operations.checklists import daily_checklist, end_of_day_checklist
from app.operations.metrics_store import operational_metrics
from app.operations.user_admin import (
    assign_role,
    create_user,
    list_users,
    reset_password,
    set_user_active,
    unlock_user,
)
from app.security.roles import ALL_ROLES
from app.models.export import ExportJob
from app.models.raw import RawUpload

router = APIRouter(prefix="/v1", tags=["v1"])


# --- Section 3: Authentication (public) ---


@router.post("/auth/login")
def auth_login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    result = login(db, body.email, body.password)
    if not result:
        raise HTTPException(status_code=401, detail={"success": False, "message": "Invalid credentials"})
    record_audit(
        db,
        action="user_login",
        user_id=body.email,
        role=result.role,
        ip_address=request.client.host if request.client else None,
        browser=request.headers.get("user-agent"),
    )
    return ok({"token": result.token, "expires": result.expires, "role": result.role})


@router.post("/auth/refresh")
def auth_refresh(body: RefreshRequest):
    result = refresh(body.token)
    if not result:
        raise HTTPException(status_code=401, detail={"success": False, "message": "Invalid refresh token"})
    return ok({"token": result.token, "expires": result.expires})


@router.post("/auth/logout")
def auth_logout(request: Request, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    record_audit(
        db,
        action="user_logout",
        user_id=user.get("email"),
        role=user.get("role"),
        ip_address=user.get("ip_address"),
        browser=user.get("browser"),
    )
    return ok({"loggedOut": True})


@router.get("/audit/logs")
def audit_logs(limit: int = 100, db: Session = Depends(get_db), _user: dict = Depends(require_settings)):
    return ok({"logs": list_audit_logs(db, limit=limit)})


# --- Section 4: Customer API ---


@router.get("/customers")
def customer_list(
    page: int = 1,
    limit: int = 100,
    state: str | None = None,
    zip: str | None = None,
    segment: str | None = None,
    purchasePower: str | None = None,
    painIndex: str | None = None,
    product: str | None = None,
    campaignPriority: str | None = None,
    upload_id: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_customer_intelligence),
):
    return ok(
        list_customers(
            db,
            page=page,
            limit=limit,
            upload_id=upload_id,
            state=state,
            zip_code=zip,
            segment=segment,
            purchase_power=purchasePower,
            pain_index=painIndex,
            product=product,
            campaign_priority=campaignPriority,
        )
    )


@router.get("/customers/{customer_id}")
def customer_detail(customer_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_customer_intelligence)):
    data = get_customer_detail(db, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Customer not found"})
    return ok(data)


@router.post("/customers/upload")
async def customer_upload(
    file: UploadFile = File(...),
    sync: bool = Query(False, description="Process upload inline (tests/small files)"),
    db: Session = Depends(get_db),
    user: dict = Depends(require_upload),
):
    content = await file.read()
    try:
        validate_upload_file(file.filename, content, file.content_type)
    except UploadRuleError as e:
        raise HTTPException(status_code=400, detail={"success": False, "message": str(e)}) from e
    file_path = save_upload_file(content, file.filename or "upload.csv")
    uploaded_by = user.get("email", "system")
    use_sync = sync or not settings.upload_async
    try:
        if use_sync:
            upload = process_upload(db, file_path, file.filename or "upload.csv", uploaded_by=uploaded_by)
        else:
            upload = enqueue_customer_upload(
                db,
                file_path=file_path,
                file_name=file.filename or "upload.csv",
                uploaded_by=uploaded_by,
            )
    except UploadValidationError as e:
        raise HTTPException(status_code=422, detail={"success": False, "message": str(e)}) from e
    record_audit(
        db,
        action="upload_customer_file",
        user_id=user.get("email"),
        role=user.get("role"),
        entity_type="upload",
        entity_id=str(upload.upload_id),
        ip_address=user.get("ip_address"),
        browser=user.get("browser"),
    )
    payload = upload_status_payload(upload)
    return ok({
        "status": payload["status"],
        "uploadId": payload["uploadId"],
        "customers": payload["customers"],
        "updated": payload["updated"],
        "warnings": payload["warnings"],
        "fileName": payload["fileName"],
        "totalRows": payload["totalRows"],
        "progressPct": payload["progressPct"],
        "async": not use_sync,
    })


@router.get("/uploads/processing-profile")
def uploads_processing_profile(
    estimated_rows: int | None = Query(None, ge=0),
    _user: dict = Depends(require_upload),
):
    return ok(get_upload_processing_profile(estimated_rows))


@router.get("/upload/{upload_id}")
def upload_detail(upload_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_upload)):
    data = get_upload_status(db, upload_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Upload not found"})
    return ok(data)


@router.post("/customers/upload/preview")
async def customer_upload_preview(file: UploadFile = File(...), db: Session = Depends(get_db), _user: dict = Depends(require_upload)):
    content = await file.read()
    try:
        validate_upload_file(file.filename, content, file.content_type)
    except UploadRuleError as e:
        raise HTTPException(status_code=400, detail={"success": False, "message": str(e)}) from e
    file_path = save_upload_file(content, file.filename or "preview.csv")
    return ok(preview_upload(db, file_path, file.filename or "preview.csv"))


class MappingStandardizeRequest(BaseModel):
    rows: list[dict]
    column_map: dict[str, str | None]


@router.get("/mapping/fields")
def mapping_fields(db: Session = Depends(get_db), _user: dict = Depends(require_upload)):
    return ok({"fields": list_field_master(db)})


@router.get("/mapping/aliases")
def mapping_aliases(
    internal_field: str | None = Query(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(require_upload),
):
    return ok({"aliases": list_field_aliases(db, internal_field=internal_field)})


@router.post("/mapping/report")
async def mapping_report(
    file: UploadFile = File(...),
    provider_template: str | None = Query(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(require_upload),
):
    content = await file.read()
    try:
        validate_upload_file(file.filename, content, file.content_type)
    except UploadRuleError as e:
        raise HTTPException(status_code=400, detail={"success": False, "message": str(e)}) from e
    return ok(mapping_report_from_file(db, content, file.filename or "report.csv", provider_template))


@router.post("/mapping/validate")
async def mapping_validate(
    file: UploadFile = File(...),
    provider_template: str | None = Query(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(require_upload),
):
    content = await file.read()
    try:
        validate_upload_file(file.filename, content, file.content_type)
    except UploadRuleError as e:
        raise HTTPException(status_code=400, detail={"success": False, "message": str(e)}) from e
    return ok(mapping_validate_from_file(db, content, file.filename or "validate.csv", provider_template))


@router.post("/mapping/standardize")
def mapping_standardize(
    body: MappingStandardizeRequest,
    _user: dict = Depends(require_upload),
):
    return ok(mapping_standardize_payload(body.rows, body.column_map))


@router.delete("/upload/{upload_id}")
def delete_upload(upload_id: str, db: Session = Depends(get_db), user: dict = Depends(require_upload)):
    upload = db.query(RawUpload).filter(RawUpload.upload_id == uuid.UUID(upload_id)).first()
    if not upload:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Upload not found"})
    record_audit(
        db,
        action="delete_upload",
        user_id=user.get("email"),
        role=user.get("role"),
        entity_type="upload",
        entity_id=upload_id,
        ip_address=user.get("ip_address"),
        browser=user.get("browser"),
    )
    db.delete(upload)
    db.commit()
    return ok({"deleted": upload_id})


@router.get("/uploads")
def uploads_list(db: Session = Depends(get_db), _user: dict = Depends(require_upload)):
    return ok({"uploads": list_uploads(db)})


# --- Section 5: Intelligence API ---


@router.get("/intelligence/customer/{customer_id}")
def intelligence_customer(customer_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_customer_intelligence)):
    data = get_customer_intelligence_with_framework(db, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Customer not found"})
    return ok(data)


@router.get("/intelligence/framework/{customer_id}")
def intelligence_framework(customer_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_customer_intelligence)):
    data = get_intelligence_framework(db, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Intelligence framework not found"})
    return ok(data)


@router.get("/intelligence/state")
def intelligence_state(
    State: str | None = None,
    state: str | None = None,
    upload_id: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_customer_intelligence),
):
    return ok(get_state_dashboard(db, upload_id, State or state))


@router.get("/intelligence/zip")
def intelligence_zip(
    ZIP: str | None = None,
    zip: str | None = None,
    upload_id: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_customer_intelligence),
):
    return ok(get_zip_dashboard(db, upload_id, ZIP or zip))


@router.get("/intelligence/product")
def intelligence_product(
    product: str | None = None,
    upload_id: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_customer_intelligence),
):
    return ok(get_product_dashboard(db, upload_id, product))


@router.get("/intelligence/recommendation/{customer_id}")
def intelligence_recommendation(customer_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_customer_intelligence)):
    data = get_full_recommendation(db, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Customer not found"})
    return ok(data)


@router.get("/intelligence/recommendation/{customer_id}/product")
def intelligence_product_recommendation(customer_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_customer_intelligence)):
    data = get_product_recommendation(db, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Customer not found"})
    return ok(data)


@router.get("/intelligence/recommendation/{customer_id}/message")
def intelligence_message_recommendation(customer_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_customer_intelligence)):
    data = get_message_recommendation(db, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Customer not found"})
    return ok(data)


@router.get("/intelligence/recommendation/{customer_id}/campaign")
def intelligence_campaign_recommendation(customer_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_customer_intelligence)):
    data = get_campaign_recommendation(db, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Customer not found"})
    return ok(data)


@router.get("/intelligence/recommendation/{customer_id}/geographic")
def intelligence_geographic_recommendation(customer_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_customer_intelligence)):
    data = get_geographic_recommendation(db, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Customer not found"})
    return ok(data)


@router.get("/intelligence/prediction/revenue/{customer_id}")
def intelligence_revenue_prediction(customer_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_customer_intelligence)):
    data = get_revenue_prediction(db, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Customer not found"})
    return ok(data)


@router.get("/intelligence/prediction/conversion/{customer_id}")
def intelligence_conversion_prediction(customer_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_customer_intelligence)):
    data = get_conversion_prediction(db, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Customer not found"})
    return ok(data)


# --- Section 6: Campaign API ---


class CampaignOpportunitySimulateRequest(BaseModel):
    mainSku: str
    additionalSkus: list[str] = []
    states: list[str] = []
    segmentFilters: dict[str, list[str]] | None = None
    uploadId: str | None = None


class AudienceExportCreateRequest(BaseModel):
    name: str | None = None
    mainSku: str
    additionalSkus: list[str] = []
    states: list[str] = []
    segmentFilters: dict[str, list[str]] | None = None
    uploadId: str | None = None
    forecastCustomers: int
    forecastRevenue: float
    predictedConversion: float
    expectedOrders: float
    geoScope: str


@router.post("/campaign/opportunity-simulate")
def campaign_opportunity_simulate(
    body: CampaignOpportunitySimulateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_dashboard),
):
    from app.campaign.opportunity_simulate import simulate_email_campaign_opportunity

    try:
        result = simulate_email_campaign_opportunity(
            db,
            body.uploadId,
            main_sku=body.mainSku,
            additional_skus=body.additionalSkus,
            states=body.states,
            segment_filters=body.segmentFilters,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"success": False, "message": str(e)}) from e
    return ok(result)


@router.post("/audience-exports")
def audience_export_create(
    body: AudienceExportCreateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_dashboard),
):
    from app.campaign.audience_export import create_audience_export

    try:
        row = create_audience_export(
            db,
            main_sku=body.mainSku,
            additional_skus=body.additionalSkus,
            states=body.states,
            segment_filters=body.segmentFilters,
            upload_id=body.uploadId,
            forecast_customers=body.forecastCustomers,
            forecast_revenue=body.forecastRevenue,
            predicted_conversion=body.predictedConversion,
            expected_orders=body.expectedOrders,
            geo_scope=body.geoScope,
            name=body.name,
            created_by=user.get("email"),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"success": False, "message": str(e)}) from e
    return ok(row)


@router.get("/audience-exports")
def audience_export_list(db: Session = Depends(get_db), _user: dict = Depends(require_export)):
    from app.campaign.audience_export import list_audience_exports

    return ok({"items": list_audience_exports(db)})


@router.delete("/audience-exports/{recommendation_id}")
def audience_export_delete(
    recommendation_id: str,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_export),
):
    from app.campaign.audience_export import delete_audience_export

    if not delete_audience_export(db, recommendation_id):
        raise HTTPException(status_code=404, detail={"success": False, "message": "Audience export not found"})
    return ok({"deleted": True, "id": recommendation_id})


@router.get("/audience-exports/{recommendation_id}/download")
def audience_export_download(recommendation_id: str, _user: dict = Depends(require_export)):
    from app.campaign.audience_export import stream_audience_csv

    try:
        file_name, body = stream_audience_csv(recommendation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"success": False, "message": str(e)}) from e

    return StreamingResponse(
        body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.get("/campaign")
def campaign_list(db: Session = Depends(get_db), _user: dict = Depends(require_campaign)):
    return ok({"campaigns": list_campaigns(db)})


@router.get("/campaign/{campaign_id}")
def campaign_get(campaign_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_campaign)):
    detail = get_campaign_detail(db, campaign_id)
    if detail.get("error"):
        raise HTTPException(status_code=404, detail={"success": False, "message": detail["error"]})
    return ok(detail)


@router.post("/campaign")
def campaign_create(body: CampaignCreateRequest, db: Session = Depends(get_db), _user: dict = Depends(require_campaign_write)):
    return ok(create_campaign(db, body))


@router.put("/campaign/{campaign_id}")
def campaign_update(
    campaign_id: str,
    body: CampaignUpdateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_campaign_write),
):
    try:
        data = update_campaign(db, campaign_id, body)
    except CampaignImmutableError as e:
        raise HTTPException(status_code=403, detail={"success": False, "message": str(e)}) from e
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Campaign not found"})
    return ok(data)


@router.delete("/campaign/{campaign_id}")
def campaign_delete(campaign_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_campaign_write)):
    try:
        if not delete_campaign(db, campaign_id):
            raise HTTPException(status_code=404, detail={"success": False, "message": "Campaign not found"})
    except CampaignImmutableError as e:
        raise HTTPException(status_code=403, detail={"success": False, "message": str(e)}) from e
    return ok({"deleted": campaign_id})


@router.get("/campaign/{campaign_id}/audience")
def campaign_audience(campaign_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_campaign)):
    data = get_campaign_audience(db, campaign_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Campaign not found"})
    return ok(data)


@router.get("/campaign/{campaign_id}/forecast")
def campaign_forecast(campaign_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_forecast)):
    data = get_campaign_forecast(db, campaign_id)
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Campaign not found"})
    return ok(data)


@router.post("/campaign/{campaign_id}/approve")
def campaign_approve(campaign_id: str, db: Session = Depends(get_db), user: dict = Depends(require_campaign_approve)):
    data = approve_campaign(db, campaign_id, approver=user.get("email"))
    if not data:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Campaign not found"})
    return ok(data)


# --- Section 7: Export API ---


@router.post("/export")
def export_customers(body: ExportRequest, db: Session = Depends(get_db), user: dict = Depends(require_export)):
    job = enqueue_export_job(
        db,
        provider_name=body.provider,
        campaign_name=body.campaignName,
        campaign_id=body.campaignId,
        upload_id=body.uploadId,
        state_filter=body.stateFilter,
        zip_filter=body.zipFilter,
        segment_filter=body.segmentFilter,
        product_filter=body.productFilter,
        user_id=user.get("email"),
        role=user.get("role"),
    )
    record_audit(
        db,
        action="export_campaign",
        user_id=user.get("email"),
        role=user.get("role"),
        entity_type="export",
        entity_id=str(job.export_id),
        ip_address=user.get("ip_address"),
        browser=user.get("browser"),
    )
    payload = export_status_payload(job)
    return ok({
        **payload,
        "status": "pending",
    })


@router.get("/export/{export_id}/status")
def export_status(export_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_export)):
    try:
        eid = uuid.UUID(export_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Export not found"}) from exc
    job = db.query(ExportJob).filter(ExportJob.export_id == eid).first()
    if not job:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Export not found"})
    return ok(export_status_payload(job))


@router.get("/export/history")
def export_history(db: Session = Depends(get_db), _user: dict = Depends(require_export)):
    jobs = db.query(ExportJob).order_by(ExportJob.created_at.desc()).limit(50).all()
    return ok({
        "history": [
            {
                "exportId": str(j.export_id),
                "provider": j.provider,
                "campaign": j.campaign,
                "fileName": j.file_name,
                "status": j.status or "completed",
                "customerCount": j.customer_count,
                "createdAt": j.created_at.isoformat() if j.created_at else None,
                "downloadUrl": f"/api/v1/export/download/{j.export_id}" if j.download_url else None,
            }
            for j in jobs
        ]
    })


@router.get("/export/preview")
def export_preview_v1(
    provider: str = "Generic CSV",
    upload_id: str | None = None,
    state_filter: str | None = None,
    zip_filter: str | None = None,
    segment_filter: str | None = None,
    product_filter: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_export),
):
    return ok(get_export_preview(db, provider, upload_id, state_filter, zip_filter, segment_filter, product_filter))


@router.get("/export/download/{export_id}")
def export_download(export_id: str, db: Session = Depends(get_db)):
    job = db.query(ExportJob).filter(ExportJob.export_id == uuid.UUID(export_id)).first()
    if not job or not job.download_url:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Export not found"})
    if job.status not in (None, "completed"):
        raise HTTPException(status_code=409, detail={"success": False, "message": f"Export status is {job.status}"})

    def iter_file():
        with open(job.download_url, "rb") as handle:
            while chunk := handle.read(1024 * 64):
                yield chunk

    filename = job.file_name or f"cios_export_{export_id[:8]}.csv"
    return StreamingResponse(iter_file(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# --- Section 8: Campaign Report API ---


@router.post("/report/upload")
async def report_upload(file: UploadFile = File(...), db: Session = Depends(get_db), user: dict = Depends(require_report_import)):
    content = await file.read()
    try:
        validate_upload_file(file.filename, content, file.content_type)
    except UploadRuleError as e:
        raise HTTPException(status_code=400, detail={"success": False, "message": str(e)}) from e
    file_path = save_upload_file(content, file.filename or "report.csv")
    try:
        report = process_campaign_report(
            db,
            file_path,
            file.filename or "report.csv",
            user_id=user.get("email"),
            role=user.get("role"),
        )
    except ImportValidationError as e:
        raise HTTPException(status_code=422, detail={"success": False, "message": "; ".join(e.errors)}) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"success": False, "message": str(e)}) from e
    record_audit(
        db,
        action="import_campaign_report",
        user_id=user.get("email"),
        role=user.get("role"),
        entity_type="report",
        entity_id=str(report.id),
        ip_address=user.get("ip_address"),
        browser=user.get("browser"),
    )
    summary = json.loads(report.summary_json) if report.summary_json else {}
    return ok({
        "reportId": str(report.id),
        "campaignId": report.campaign_id,
        "status": report.status,
        "summary": summary,
    })


@router.get("/report/{campaign_id}")
def report_performance(campaign_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_campaign)):
    return ok(get_campaign_dashboard(db, campaign_id))


@router.get("/report/dashboard/{campaign_id}")
def report_dashboard(campaign_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_campaign)):
    detail = get_campaign_detail(db, campaign_id)
    if detail.get("error"):
        raise HTTPException(status_code=404, detail={"success": False, "message": detail["error"]})
    return ok(detail)


# --- Section 9: Dashboard API ---


@router.get("/dashboard/executive")
def dashboard_executive(upload_id: str | None = None, db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok(get_executive_summary(db, upload_id))


@router.get("/dashboard/customer")
def dashboard_customer(upload_id: str | None = None, limit: int = 500, db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok({
        "distribution": get_customer_distribution(db, upload_id),
        "customers": get_customer_table(db, upload_id, limit=limit),
    })


@router.get("/dashboard/state")
def dashboard_state(
    state: str | None = None,
    upload_id: str | None = None,
    zip_limit: int | None = Query(default=None),
    lite: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: dict = Depends(require_dashboard),
):
    return ok(get_state_dashboard(db, upload_id, state, zip_limit=zip_limit, lite=lite))


@router.get("/dashboard/metro")
def dashboard_metro(
    cbsa: str | None = None,
    upload_id: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_dashboard),
):
    return ok(get_metro_intelligence_dashboard(db, upload_id, cbsa))


@router.get("/geo/zcta")
def geo_zcta_choropleth(
    state: str | None = Query(default=None, min_length=2, max_length=2),
    cbsa: str | None = Query(default=None),
    upload_id: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_dashboard),
):
    if cbsa:
        return ok(get_metro_zcta_choropleth(db, upload_id, cbsa))
    if not state:
        raise HTTPException(status_code=422, detail="state or cbsa is required")
    return ok(get_state_zcta_choropleth(db, upload_id, state.upper()))


@router.get("/dashboard/zip")
def dashboard_zip(zip: str | None = None, upload_id: str | None = None, db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok(get_zip_dashboard(db, upload_id, zip))


@router.get("/dashboard/product")
def dashboard_product(product: str | None = None, upload_id: str | None = None, db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok(get_product_dashboard(db, upload_id, product))


@router.get("/dashboard/roi")
def dashboard_roi(db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok(get_roi_dashboard(db))


@router.get("/dashboard/campaigns")
def dashboard_campaigns(campaign_id: str | None = None, db: Session = Depends(get_db), _user: dict = Depends(require_campaign)):
    return ok(get_campaign_dashboard(db, campaign_id))


# --- Section 10: Forecast API ---


@router.get("/forecast/revenue")
def forecast_revenue(
    targetCustomers: int = 1000,
    campaignType: str = "Email",
    db: Session = Depends(get_db),
    _user: dict = Depends(require_forecast),
):
    return ok(compute_campaign_forecast(target_customers=targetCustomers, campaign_type=campaignType))


@router.get("/forecast/conversion")
def forecast_conversion(targetCustomers: int = 1000, db: Session = Depends(get_db), _user: dict = Depends(require_forecast)):
    result = compute_campaign_forecast(target_customers=targetCustomers)
    return ok({
        "targetCustomers": targetCustomers,
        "expectedConversion": result["expected_conversion"],
        "expectedOrders": result["expected_orders"],
        "forecastConfidence": result["forecast_confidence"],
    })


@router.get("/forecast/product")
def forecast_product(product: str = "Master V9", targetCustomers: int = 100, db: Session = Depends(get_db), _user: dict = Depends(require_forecast)):
    result = compute_campaign_forecast(
        target_customers=targetCustomers,
        product_distribution={product: targetCustomers},
    )
    return ok({"product": product, **result})


# --- Section 11: Settings API ---


@router.get("/settings")
def settings_all(db: Session = Depends(get_db), _user: dict = Depends(require_settings)):
    return ok(get_settings_info(db))


@router.get("/settings/rules")
def settings_rules(db: Session = Depends(get_db), _user: dict = Depends(require_rule_library)):
    info = get_settings_info(db)
    return ok(info["intelligence"])


@router.get("/settings/mapping")
def settings_mapping(db: Session = Depends(get_db), _user: dict = Depends(require_settings)):
    return ok({"mappingVersion": get_settings_info(db)["intelligence"]["mapping_version"]})


@router.get("/settings/reference")
def settings_reference(db: Session = Depends(get_db), _user: dict = Depends(require_settings)):
    return ok(get_reference_version(db))


@router.get("/reference")
def reference_overview(db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok(get_reference_catalog(db))


@router.get("/reference/products")
def reference_products(db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok({"products": get_products(db), "prices": get_product_prices(db)})


@router.get("/reference/segments")
def reference_segments(db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok({
        "ceragemSegments": list(get_ceragem_segments(db)),
        "prizmSegments": get_prizm_segments(db),
        "audienceSegments": get_audience_segments(),
        "purchasePowerLevels": list(get_purchase_power_levels(db)),
    })


@router.get("/reference/geographic")
def reference_geographic(db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok(get_geographic_summary(db))


@router.get("/reference/providers")
def reference_providers(db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok({"providers": list(get_providers(db))})


@router.get("/reference/dashboards")
def reference_dashboards(db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok(get_dashboard_config(db))


@router.get("/learning/insights")
def learning_insights_v1(limit: int = 20, db: Session = Depends(get_db), _user: dict = Depends(require_campaign)):
    from app.campaign.analytics import get_learning_insights
    return ok({"insights": get_learning_insights(db, limit)})


# --- Volume 17: Analytics & Executive Intelligence ---


def _analytics_filters(
    upload_id: str | None = None,
    campaign_id: str | None = None,
    state: str | None = None,
    zip: str | None = None,
    product: str | None = None,
    provider: str | None = None,
    campaign_type: str | None = None,
    segment: str | None = None,
):
    from app.analytics.filters import AnalyticsFilters

    return AnalyticsFilters(
        upload_id=upload_id,
        campaign_id=campaign_id,
        state=state,
        zip_code=zip,
        product=product,
        provider=provider,
        campaign_type=campaign_type,
        segment=segment,
    )


@router.get("/analytics/executive")
def analytics_executive(
    upload_id: str | None = None,
    campaign_id: str | None = None,
    state: str | None = None,
    zip: str | None = None,
    product: str | None = None,
    provider: str | None = None,
    campaign_type: str | None = None,
    segment: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_dashboard),
):
    from app.analytics.executive import get_executive_intelligence

    filters = _analytics_filters(upload_id, campaign_id, state, zip, product, provider, campaign_type, segment)
    return ok(get_executive_intelligence(db, filters))


@router.get("/analytics/insights")
def analytics_insights(
    upload_id: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_dashboard),
):
    from app.analytics.insights import generate_business_insights

    return ok({"insights": generate_business_insights(db, _analytics_filters(upload_id=upload_id, state=state))})


@router.get("/analytics/recommendations")
def analytics_recommendations(
    upload_id: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_dashboard),
):
    from app.analytics.recommendations import generate_executive_recommendations

    return ok({"recommendations": generate_executive_recommendations(db, _analytics_filters(upload_id=upload_id))})


@router.get("/analytics/compare")
def analytics_compare(
    type: str,
    a: str,
    b: str,
    upload_id: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_dashboard),
):
    from app.analytics.comparative import compare_entities

    return ok(compare_entities(db, type, a, b, upload_id))


@router.get("/analytics/trends")
def analytics_trends(
    metric: str = "revenue",
    period: str = "month",
    db: Session = Depends(get_db),
    _user: dict = Depends(require_dashboard),
):
    from app.analytics.trends import get_trend_analysis

    return ok(get_trend_analysis(db, metric, period))


@router.get("/analytics/learning")
def analytics_learning(limit: int = 20, db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    from app.analytics.learning_intel import get_learning_intelligence

    return ok(get_learning_intelligence(db, limit))


@router.get("/analytics/scorecard")
def analytics_scorecard(
    upload_id: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_dashboard),
):
    from app.analytics.scorecard import get_executive_scorecard

    return ok(get_executive_scorecard(db, _analytics_filters(upload_id=upload_id)))


@router.get("/analytics/alerts")
def analytics_alerts(
    upload_id: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_dashboard),
):
    from app.analytics.alerts import get_executive_alerts

    return ok({"alerts": get_executive_alerts(db, _analytics_filters(upload_id=upload_id))})


@router.post("/analytics/reports/generate")
def analytics_reports_generate(
    body: AnalyticsReportRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_dashboard),
):
    from app.analytics.reports import generate_executive_report

    try:
        report = generate_executive_report(
            db,
            report_type=body.report_type,
            frequency=body.frequency,
            output_format=body.output_format,
            filters=_analytics_filters(body.upload_id, body.campaign_id, body.state),
            created_by=user.get("email"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"success": False, "message": str(e)}) from e
    return ok({
        "reportId": str(report.report_id),
        "reportType": report.report_type,
        "frequency": report.frequency,
        "format": report.output_format,
        "fileName": report.file_name,
        "status": report.status,
    })


@router.get("/analytics/reports")
def analytics_reports_list(limit: int = 20, db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    from app.analytics.reports import list_reports

    return ok({"reports": list_reports(db, limit)})


@router.get("/analytics/reports/{report_id}")
def analytics_reports_detail(report_id: str, db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    from app.analytics.reports import get_report

    report = get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Report not found"})
    return ok({
        "reportId": str(report.report_id),
        "reportType": report.report_type,
        "frequency": report.frequency,
        "format": report.output_format,
        "fileName": report.file_name,
        "status": report.status,
        "summary": json.loads(report.summary_json) if report.summary_json else {},
        "createdAt": report.created_at.isoformat() if report.created_at else None,
    })


@router.get("/analytics/export")
def analytics_export(
    upload_id: str | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_dashboard),
):
    from fastapi.responses import Response

    from app.analytics.reports import export_analytics_csv

    csv_data = export_analytics_csv(db, _analytics_filters(upload_id=upload_id))
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=executive_kpis.csv"},
    )


@router.get("/reports")
def reports_list(db: Session = Depends(get_db), _user: dict = Depends(require_report_import)):
    return ok({"reports": list_campaign_reports(db)})


# --- Volume 20: Le Frame Customer Intelligence Methodology ---


@router.get("/methodology")
def methodology_overview(db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok(get_methodology_overview(db))


@router.get("/methodology/pyramid")
def methodology_pyramid(_user: dict = Depends(require_dashboard)):
    return ok(get_methodology_pyramid())


@router.get("/methodology/layers")
def methodology_layers(_user: dict = Depends(require_dashboard)):
    return ok(get_methodology_layers())


@router.get("/methodology/governance")
def methodology_governance(_user: dict = Depends(require_dashboard)):
    return ok(get_methodology_governance())


@router.get("/methodology/success-criteria")
def methodology_success_criteria(db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok(get_methodology_success_criteria(db))


# --- Volume 21: Master Index & Knowledge Governance ---


@router.get("/conventions")
def conventions_overview(_user: dict = Depends(require_dashboard)):
    return ok(get_conventions_overview())


@router.get("/conventions/compliance")
def conventions_compliance(_user: dict = Depends(require_dashboard)):
    import os

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    return ok(verify_convention_compliance(root))


@router.get("/git-workflow")
def git_workflow_overview(_user: dict = Depends(require_dashboard)):
    return ok(get_git_workflow_overview())


@router.get("/git-workflow/compliance")
def git_workflow_compliance(_user: dict = Depends(require_dashboard)):
    import os

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    return ok(verify_git_workflow_compliance(root))


@router.get("/design-principles")
def design_principles_overview(_user: dict = Depends(require_dashboard)):
    return ok(get_design_principles_overview())


@router.get("/design-principles/compliance")
def design_principles_compliance(_user: dict = Depends(require_dashboard)):
    import os

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    return ok(verify_design_principles_compliance(root))


@router.get("/knowledge")
def knowledge_overview(db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok(get_knowledge_overview(db))


@router.get("/knowledge/index")
def knowledge_index(_user: dict = Depends(require_dashboard)):
    return ok(get_knowledge_index())


@router.get("/knowledge/cross-reference")
def knowledge_cross_reference(_user: dict = Depends(require_dashboard)):
    return ok(get_knowledge_cross_reference())


@router.get("/knowledge/governance")
def knowledge_governance(_user: dict = Depends(require_dashboard)):
    return ok(get_knowledge_governance())


@router.get("/knowledge/glossary")
def knowledge_glossary(_user: dict = Depends(require_dashboard)):
    return ok(get_knowledge_glossary())


@router.get("/knowledge/acceptance-criteria")
def knowledge_acceptance_criteria(db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    return ok(get_knowledge_acceptance_criteria(db))


# --- Commercial Intelligence API ---


class CommercialSimulateRequest(BaseModel):
    product: str
    targetCustomers: int = 1000
    sellingPrice: float | None = None
    promotionPct: float | None = None
    maxPromotion: float | None = None
    promoCode: str | None = None
    leFrameIncentiveRate: float | None = None
    corporatePriority: float = 0.5
    inventoryUnits: int | None = None


@router.get("/commercial/catalog")
def commercial_catalog_snapshot(db: Session = Depends(get_db), _user: dict = Depends(require_settings)):
    from app.commercial.admin import get_catalog_snapshot

    return ok(get_catalog_snapshot(db))


class CommercialCatalogSaveRequest(BaseModel):
    products: list[dict]
    notes: str | None = None
    publish: bool = True


@router.put("/commercial/catalog")
def commercial_catalog_save(
    body: CommercialCatalogSaveRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_settings),
):
    from app.commercial.admin import save_catalog

    result = save_catalog(
        db,
        body.products,
        created_by=user.get("email"),
        notes=body.notes,
        publish=body.publish,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail={"success": False, "message": "; ".join(result.get("errors", []))})
    record_audit(
        db,
        action="publish_commercial_catalog" if body.publish else "save_commercial_catalog_draft",
        user_id=user.get("email"),
        role=user.get("role"),
        entity_type="commercial_catalog",
        entity_id=result.get("version_id"),
        ip_address=user.get("ip_address"),
        browser=user.get("browser"),
    )
    return ok(result)


@router.get("/commercial/price-guide")
def commercial_price_guide_export(db: Session = Depends(get_db), _user: dict = Depends(require_dashboard)):
    from app.commercial.admin import catalog_to_csv_rows
    from app.commercial.catalog import get_effective_catalog

    csv_data = catalog_to_csv_rows(get_effective_catalog())
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="commercial_price_guide.csv"'},
    )


@router.get("/commercial/versions")
def commercial_versions(db: Session = Depends(get_db), _user: dict = Depends(require_settings)):
    from app.commercial.admin import list_catalog_versions

    return ok({"versions": list_catalog_versions(db)})


@router.post("/commercial/price-guide/import")
async def commercial_price_guide_import(
    file: UploadFile = File(...),
    version: str | None = Form(None),
    notes: str | None = Form(None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_settings),
):
    from app.commercial.admin import import_catalog_csv

    content = (await file.read()).decode("utf-8-sig")
    result = import_catalog_csv(
        db,
        content,
        version=version,
        created_by=user.get("email"),
        notes=notes,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail={"success": False, "message": "; ".join(result.get("errors", []))})
    record_audit(
        db,
        action="import_commercial_price_guide",
        user_id=user.get("email"),
        role=user.get("role"),
        entity_type="commercial_catalog",
        entity_id=result.get("version_id"),
        ip_address=user.get("ip_address"),
        browser=user.get("browser"),
    )
    return ok(result)


@router.post("/commercial/versions/{version_id}/approve")
def commercial_version_approve(
    version_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_settings),
):
    from app.commercial.admin import approve_catalog_version

    try:
        result = approve_catalog_version(db, version_id, approved_by=user.get("email"))
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"success": False, "message": str(e)}) from e
    record_audit(
        db,
        action="approve_commercial_catalog",
        user_id=user.get("email"),
        role=user.get("role"),
        entity_type="commercial_catalog",
        entity_id=version_id,
        ip_address=user.get("ip_address"),
        browser=user.get("browser"),
    )
    return ok(result)


@router.post("/commercial/versions/{version_id}/rollback")
def commercial_version_rollback(
    version_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_settings),
):
    from app.commercial.admin import rollback_catalog_version

    try:
        result = rollback_catalog_version(db, version_id, approved_by=user.get("email"))
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"success": False, "message": str(e)}) from e
    record_audit(
        db,
        action="rollback_commercial_catalog",
        user_id=user.get("email"),
        role=user.get("role"),
        entity_type="commercial_catalog",
        entity_id=version_id,
        ip_address=user.get("ip_address"),
        browser=user.get("browser"),
    )
    return ok(result)


@router.post("/commercial/simulate")
def commercial_simulate(body: CommercialSimulateRequest, _user: dict = Depends(require_dashboard)):
    from app.commercial.simulator import simulate_commercial_scenario

    try:
        result = simulate_commercial_scenario(
            product_code=body.product,
            target_customers=body.targetCustomers,
            selling_price=body.sellingPrice,
            promotion_pct=body.promotionPct,
            max_promotion=body.maxPromotion,
            promo_code=body.promoCode,
            le_frame_incentive_rate=body.leFrameIncentiveRate,
            corporate_priority=body.corporatePriority,
            inventory_units=body.inventoryUnits,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"success": False, "message": str(e)}) from e
    return ok(result)


# --- Volume 14: System Administration ---


@router.get("/admin/dashboard")
def admin_dashboard(db: Session = Depends(get_db), _user: dict = Depends(require_user_admin)):
    return ok(get_admin_dashboard(db))


@router.get("/admin/metrics")
def admin_metrics(_user: dict = Depends(require_user_admin)):
    return ok(operational_metrics())


@router.get("/admin/checklists/daily")
def admin_daily_checklist(db: Session = Depends(get_db), _user: dict = Depends(require_user_admin)):
    return ok(daily_checklist(db))


@router.get("/admin/checklists/end-of-day")
def admin_eod_checklist(db: Session = Depends(get_db), _user: dict = Depends(require_user_admin)):
    return ok(end_of_day_checklist(db))


@router.get("/admin/users")
def admin_users_list(db: Session = Depends(get_db), _user: dict = Depends(require_user_admin)):
    return ok({"users": list_users(db), "roles": sorted(ALL_ROLES)})


@router.post("/admin/users")
def admin_users_create(body: UserCreateRequest, db: Session = Depends(get_db), user: dict = Depends(require_user_admin)):
    try:
        data = create_user(db, email=str(body.email), password=body.password, name=body.name, role=body.role, actor=user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"success": False, "message": str(e)}) from e
    return ok(data)


@router.put("/admin/users/{email}/role")
def admin_users_role(email: str, body: UserRoleRequest, db: Session = Depends(get_db), user: dict = Depends(require_user_admin)):
    try:
        data = assign_role(db, email, body.role, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"success": False, "message": str(e)}) from e
    return ok(data)


@router.post("/admin/users/{email}/reset-password")
def admin_users_reset_password(
    email: str, body: UserPasswordRequest, db: Session = Depends(get_db), user: dict = Depends(require_user_admin)
):
    try:
        data = reset_password(db, email, body.password, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"success": False, "message": str(e)}) from e
    return ok(data)


@router.post("/admin/users/{email}/disable")
def admin_users_disable(email: str, db: Session = Depends(get_db), user: dict = Depends(require_user_admin)):
    try:
        data = set_user_active(db, email, False, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"success": False, "message": str(e)}) from e
    return ok(data)


@router.post("/admin/users/{email}/activate")
def admin_users_activate(email: str, db: Session = Depends(get_db), user: dict = Depends(require_user_admin)):
    try:
        data = set_user_active(db, email, True, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"success": False, "message": str(e)}) from e
    return ok(data)


@router.post("/admin/users/{email}/unlock")
def admin_users_unlock(email: str, db: Session = Depends(get_db), user: dict = Depends(require_user_admin)):
    try:
        data = unlock_user(db, email, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"success": False, "message": str(e)}) from e
    return ok(data)


@router.get("/admin/providers")
def admin_providers(db: Session = Depends(get_db), _user: dict = Depends(require_user_admin)):
    return ok({"providers": list_providers(db), "readOnlyRules": True})


@router.get("/providers")
def providers_list(db: Session = Depends(get_db), _user: dict = Depends(require_export)):
    return ok({"providers": list_providers(db)})


@router.get("/providers/{provider_name}")
def providers_detail(provider_name: str, db: Session = Depends(get_db), _user: dict = Depends(require_export)):
    detail = get_provider(db, provider_name)
    if not detail:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Provider not found"})
    return ok(detail)
