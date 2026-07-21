"""Volume 17 Section 22 — Global analytics filter parameters."""

from dataclasses import dataclass


@dataclass
class AnalyticsFilters:
    upload_id: str | None = None
    campaign_id: str | None = None
    state: str | None = None
    zip_code: str | None = None
    product: str | None = None
    provider: str | None = None
    campaign_type: str | None = None
    segment: str | None = None
    customer_type: str | None = None
    purchase_power: str | None = None
    pain_index: str | None = None
    lifestyle: str | None = None
    date_from: str | None = None
    date_to: str | None = None
