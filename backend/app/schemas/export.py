from pydantic import BaseModel


class ExportRequest(BaseModel):
    provider: str = "Generic CSV"
    campaignId: str = "CAMP-001"
    campaignName: str = "Ceragem Campaign"
    uploadId: str | None = None
    stateFilter: str | None = None
    zipFilter: str | None = None
    segmentFilter: str | None = None
    productFilter: str | None = None
