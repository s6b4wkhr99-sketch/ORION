from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.acquisition.preview import preview_upload
from app.acquisition.upload import UploadValidationError, process_upload, save_upload_file
from app.rules.upload import UploadRuleError, validate_upload_file
from app.campaign.analytics import (
    get_campaign_dashboard,
    get_customer_distribution,
    get_customer_table,
    get_executive_summary,
    get_learning_insights,
    get_retail_intelligence,
    list_campaign_reports,
    list_uploads,
)
from app.campaign.detail import get_campaign_detail
from app.campaign.dashboards import (
    get_export_preview,
    get_product_dashboard,
    get_roi_dashboard,
    get_settings_info,
    get_state_dashboard,
    get_zip_dashboard,
)
from app.campaign.export import generate_export
from app.campaign.reports import process_campaign_report
from app.database import get_db

router = APIRouter()


@router.post("/uploads/preview")
async def preview_customer_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        validate_upload_file(file.filename, content)
    except UploadRuleError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    file_path = save_upload_file(content, file.filename or "preview.csv")
    preview = preview_upload(db, file_path, file.filename)
    return preview


@router.post("/uploads")
async def upload_customers(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        validate_upload_file(file.filename, content)
    except UploadRuleError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    file_path = save_upload_file(content, file.filename or "upload.csv")
    try:
        upload = process_upload(db, file_path, file.filename)
    except UploadValidationError as e:
        raise HTTPException(status_code=422, detail={"message": str(e), "validation": e.details})
    summary = upload.summary_json and __import__("json").loads(upload.summary_json)
    return {
        "upload_id": str(upload.upload_id),
        "file_name": upload.filename,
        "status": upload.status,
        "summary": summary,
    }


@router.get("/uploads")
def get_uploads(db: Session = Depends(get_db)):
    return {"uploads": list_uploads(db)}


@router.post("/campaign-reports")
async def upload_campaign_report(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")
    ext = file.filename.lower().split(".")[-1]
    if ext not in {"csv", "xlsx", "xls"}:
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported")

    content = await file.read()
    file_path = save_upload_file(content, file.filename)
    try:
        report = process_campaign_report(db, file_path, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    summary = report.summary_json and __import__("json").loads(report.summary_json)
    return {
        "report_id": str(report.id),
        "file_name": report.file_name,
        "campaign_id": report.campaign_id,
        "campaign_name": report.campaign_id,
        "status": report.status,
        "summary": summary,
    }


@router.get("/campaign-reports")
def get_campaign_reports(db: Session = Depends(get_db)):
    return {"reports": list_campaign_reports(db)}


@router.get("/analytics/executive")
def executive_dashboard(upload_id: str | None = None, db: Session = Depends(get_db)):
    return get_executive_summary(db, upload_id)


@router.get("/analytics/customers")
def customer_dashboard(
    upload_id: str | None = None,
    limit: int = 500,
    db: Session = Depends(get_db),
):
    distribution = get_customer_distribution(db, upload_id)
    table = get_customer_table(db, upload_id, limit=limit)
    return {"distribution": distribution, "customers": table}


@router.get("/analytics/customers/table")
def customer_table(
    upload_id: str | None = None,
    state: str | None = None,
    segment: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return get_customer_table(db, upload_id, state, segment, limit, offset)


@router.get("/analytics/retail")
def retail_dashboard(
    upload_id: str | None = None,
    state: str | None = None,
    segment: str | None = None,
    product: str | None = None,
    db: Session = Depends(get_db),
):
    return get_retail_intelligence(db, upload_id, state, segment, product)


@router.get("/analytics/campaigns")
def campaign_dashboard(campaign_id: str | None = None, db: Session = Depends(get_db)):
    return get_campaign_dashboard(db, campaign_id)


@router.get("/analytics/campaigns/{campaign_id}/detail")
def campaign_detail(campaign_id: str, db: Session = Depends(get_db)):
    result = get_campaign_detail(db, campaign_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/campaigns")
def create_campaign(
    campaign_name: str = Form(...),
    campaign_type: str = Form("Email"),
    provider: str = Form("mass_email"),
    db: Session = Depends(get_db),
):
    import uuid as uuid_mod
    from app.models.campaign import Campaign

    campaign_id = f"CAMP-{uuid_mod.uuid4().hex[:8].upper()}"
    campaign = Campaign(
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        campaign_type=campaign_type,
        status="draft",
        provider=provider,
        owner="CIOS Admin",
        forecast_version="Volume 06 v1.0",
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return {
        "campaign_id": campaign.campaign_id,
        "campaign_name": campaign.campaign_name,
        "status": campaign.status,
    }


@router.get("/learning/insights")
def learning_insights(limit: int = 20, db: Session = Depends(get_db)):
    return {"insights": get_learning_insights(db, limit)}


@router.get("/analytics/states")
def state_dashboard(
    upload_id: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
):
    return get_state_dashboard(db, upload_id, state)


@router.get("/analytics/zip-detail")
def zip_dashboard(
    upload_id: str | None = None,
    zip: str | None = None,
    db: Session = Depends(get_db),
):
    return get_zip_dashboard(db, upload_id, zip)


@router.get("/analytics/products")
def product_dashboard(
    upload_id: str | None = None,
    product: str | None = None,
    db: Session = Depends(get_db),
):
    return get_product_dashboard(db, upload_id, product)


@router.get("/analytics/roi")
def roi_dashboard(db: Session = Depends(get_db)):
    return get_roi_dashboard(db)


@router.get("/export/preview")
def export_preview(
    provider: str = "Generic CSV",
    upload_id: str | None = None,
    state_filter: str | None = None,
    zip_filter: str | None = None,
    segment_filter: str | None = None,
    product_filter: str | None = None,
    db: Session = Depends(get_db),
):
    return get_export_preview(db, provider, upload_id, state_filter, zip_filter, segment_filter, product_filter)


@router.get("/settings")
def settings_info(db: Session = Depends(get_db)):
    return get_settings_info(db)


@router.post("/export")
def create_export(
    provider_name: str = Form("Generic CSV"),
    campaign_name: str = Form("Ceragem Campaign"),
    campaign_id: str = Form("CAMP-001"),
    state_filter: str | None = Form(None),
    zip_filter: str | None = Form(None),
    segment_filter: str | None = Form(None),
    product_filter: str | None = Form(None),
    message_direction_filter: str | None = Form(None),
    upload_id: str | None = Form(None),
    db: Session = Depends(get_db),
):
    file_path, job = generate_export(
        db,
        provider_name=provider_name,
        campaign_name=campaign_name,
        campaign_id=campaign_id,
        state_filter=state_filter or None,
        zip_filter=zip_filter or None,
        segment_filter=segment_filter or None,
        product_filter=product_filter or None,
        message_direction_filter=message_direction_filter or None,
        upload_id=upload_id or None,
    )
    return {
        "export_id": str(job.export_id),
        "file_url": f"/api/export/download/{job.export_id}",
        "row_count": "see file",
    }


@router.get("/export/download/{export_id}")
def download_export(export_id: str, db: Session = Depends(get_db)):
    from app.models.export import ExportJob
    import uuid

    job = db.query(ExportJob).filter(ExportJob.export_id == uuid.UUID(export_id)).first()
    if not job or not job.download_url:
        raise HTTPException(status_code=404, detail="Export not found")
    return FileResponse(job.download_url, filename=f"cios_export_{export_id[:8]}.csv", media_type="text/csv")
