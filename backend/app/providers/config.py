"""Volume 15 Sections 8–13 & 16 — Provider mapping configuration (no business logic)."""

from app.providers.constants import SUPPORTED_PROVIDERS

# Internal metric fields (Section 16) — provider terminology never stored raw
INTERNAL_METRICS: tuple[str, ...] = (
    "total_sent",
    "delivered",
    "opened",
    "unique_open",
    "clicked",
    "unique_click",
    "actual_revenue",
    "actual_orders",
    "bounce",
    "unsubscribe",
)

# Section 16 — provider column aliases → internal metric
METRIC_ALIASES: dict[str, list[str]] = {
    "total_sent": ["sent", "emails sent", "total sent", "send"],
    "delivered": ["delivered", "emails delivered"],
    "opened": ["open", "opens", "opened", "total open"],
    "unique_open": ["unique open", "unique opens", "unique_open", "unique opens"],
    "clicked": ["click", "clicks", "clicked", "total click", "total clicks"],
    "unique_click": ["unique click", "unique_click", "unique clicks"],
    "actual_revenue": ["revenue", "sales", "total revenue"],
    "actual_orders": ["conversion", "conversions", "orders", "actual orders"],
    "bounce": ["bounce", "bounces", "hard bounce", "soft bounce"],
    "unsubscribe": ["unsubscribe", "unsubscribes", "opt-out", "opt out", "opt-out"],
}

# Provider-specific import metric overlays (Sections 9–13)
PROVIDER_IMPORT_METRICS: dict[str, list[str]] = {
    "Klaviyo": ["delivered", "opened", "clicked", "unique_click", "bounce", "actual_revenue"],
    "Mailchimp": ["total_sent", "opened", "clicked", "bounce", "unsubscribe", "actual_revenue"],
    "HubSpot": ["delivered", "opened", "clicked", "actual_revenue", "actual_orders"],
    "Salesforce Marketing Cloud": ["delivered", "opened", "clicked", "actual_revenue"],
    "Attentive": ["delivered", "opened", "clicked", "actual_revenue", "actual_orders", "unsubscribe"],
    "Generic CSV": list(INTERNAL_METRICS),
}

# Export required internal fields per provider (Section 14)
PROVIDER_EXPORT_REQUIRED: dict[str, list[str]] = {
    "Generic CSV": ["email_address", "campaign_id", "recommended_product", "message_direction"],
    "Klaviyo": ["email_address", "campaign_name", "campaign_id", "recommended_product"],
    "Mailchimp": ["email_address", "campaign_name", "campaign_id"],
    "HubSpot": ["email_address", "campaign_name", "recommended_product"],
    "Salesforce Marketing Cloud": ["email_address", "campaign_id", "recommended_product"],
    "Attentive": ["email_address", "campaign_name", "recommended_product"],
}

# Header signatures for provider detection on import (Section 6)
PROVIDER_IMPORT_SIGNATURES: dict[str, set[str]] = {
    "Mailchimp": {"sent", "open", "click", "bounce", "fname", "lname", "email address", "email"},
    "Klaviyo": {"delivered", "opened", "clicked", "unique click", "sent", "open", "click"},
    "HubSpot": {"firstname", "lastname", "delivered", "conversion", "open", "click"},
    "Salesforce Marketing Cloud": {"subscriberkey", "emailaddress", "journey", "campaignid"},
    "Attentive": {"opt-out", "opt out", "phone", "conversion", "delivered"},
}

# Extra export template rows beyond data_dictionary seed (provider-specific labels)
PROVIDER_EXPORT_EXTENSIONS: list[tuple[str, str, str, int, bool]] = [
    ("Generic CSV", "email_address", "Email", 0, True),
    ("Generic CSV", "state", "State", 6, False),
    ("Generic CSV", "zip_code", "ZIP", 7, False),
    ("Klaviyo", "ceragem_segment", "Segment", 10, False),
    ("Klaviyo", "campaign_name", "Campaign Name", 11, False),
    ("Klaviyo", "campaign_id", "Campaign ID", 12, False),
    ("Mailchimp", "state", "State", 5, False),
    ("Mailchimp", "campaign_name", "Campaign Name", 10, False),
    ("Mailchimp", "campaign_id", "Campaign ID", 11, False),
    ("HubSpot", "state", "State", 5, False),
    ("HubSpot", "campaign_name", "Campaign", 10, False),
    ("HubSpot", "recommended_product", "Product", 11, False),
    ("Salesforce Marketing Cloud", "email_address", "SubscriberKey", 0, True),
    ("Salesforce Marketing Cloud", "ceragem_segment", "Segment", 10, False),
    ("Salesforce Marketing Cloud", "recommended_product", "RecommendedProduct", 11, False),
    ("Salesforce Marketing Cloud", "campaign_id", "CampaignID", 12, False),
    ("Attentive", "campaign_name", "Campaign", 10, False),
    ("Attentive", "ceragem_segment", "Segment", 11, False),
    ("Attentive", "recommended_product", "Product", 12, False),
]

PROVIDER_METADATA: dict[str, dict] = {
    name: {
        "exportFormat": "CSV",
        "encoding": "UTF-8",
        "delimiter": ",",
        "headerRequired": True,
        "primaryIdentifier": "email_address",
        "importMetrics": PROVIDER_IMPORT_METRICS.get(name, []),
        "exportRequiredFields": PROVIDER_EXPORT_REQUIRED.get(name, ["email_address"]),
    }
    for name in SUPPORTED_PROVIDERS
}
