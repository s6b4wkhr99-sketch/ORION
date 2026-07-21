"""Volume 17 — Analytics API schemas."""

from pydantic import BaseModel, Field


class AnalyticsReportRequest(BaseModel):
    report_type: str = Field(default="daily_executive")
    frequency: str = Field(default="daily")
    output_format: str = Field(default="csv", alias="format")
    upload_id: str | None = None
    state: str | None = None
    campaign_id: str | None = None

    model_config = {"populate_by_name": True}


class AnalyticsCompareQuery(BaseModel):
    type: str
    a: str
    b: str
    upload_id: str | None = None
