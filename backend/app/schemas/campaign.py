from pydantic import BaseModel


class CampaignCreateRequest(BaseModel):
    campaignName: str
    campaignType: str = "Product Promotion"
    provider: str = "mass_email"


class CampaignUpdateRequest(BaseModel):
    campaignName: str | None = None
    campaignType: str | None = None
    status: str | None = None
    budget: float | None = None
    provider: str | None = None
