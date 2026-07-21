"""
Volume 09 — Field Mapping & Data Dictionary (Single Source of Truth).

All modules must reference internal field names defined here.
Database column names may differ via INTERNAL_TO_DB for backward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class FieldCategory(str, Enum):
    CUSTOMER = "customer"
    GEOGRAPHIC = "geographic"
    DATALOGIX = "datalogix"
    INTELLIGENCE = "intelligence"
    CAMPAIGN = "campaign"
    FORECAST = "forecast"
    PROVIDER = "provider"
    PERFORMANCE = "performance"
    LEARNING = "learning"
    ZIP_INTELLIGENCE = "zip_intelligence"


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    category: FieldCategory
    data_type: str
    required: bool = False
    description: str = ""
    db_column: str | None = None
    read_only: bool = False


# Legacy DB columns retained for backward compatibility (Volume 09 §23).
INTERNAL_TO_DB: dict[str, str] = {
    "email_address": "email",
    "zip_code": "zip",
    "net_worth_indicator": "net_worth",
    "dwelling_type": "dwelling",
    "household_composition": "household",
    "contact_permission": "permission",
    "segment_id": "sfmc_segment_id",
    "segment_code": "sfmc_segment_code",
    "segment_name": "sfmc_segment_name",
    "campaign_status": "status",
    "campaign_owner": "owner",
    "total_sent": "sent",
    "opened": "open",
    "clicked": "click",
    "actual_revenue": "revenue",
}

DB_TO_INTERNAL: dict[str, str] = {v: k for k, v in INTERNAL_TO_DB.items()}


def db_column(internal: str) -> str:
    return INTERNAL_TO_DB.get(internal, internal)


def internal_name(db_col: str) -> str:
    return DB_TO_INTERNAL.get(db_col, db_col)


# --- Section 5: Customer Master ---
CUSTOMER_FIELDS: tuple[FieldDefinition, ...] = (
    FieldDefinition("customer_id", FieldCategory.CUSTOMER, "uuid", True, "Internal customer identifier", read_only=True),
    FieldDefinition("email_address", FieldCategory.CUSTOMER, "string", True, "Primary email", "email"),
    FieldDefinition("first_name", FieldCategory.CUSTOMER, "string", False, "First name"),
    FieldDefinition("last_name", FieldCategory.CUSTOMER, "string", False, "Last name"),
    FieldDefinition("phone", FieldCategory.CUSTOMER, "string", False, "Phone number"),
    FieldDefinition("created_at", FieldCategory.CUSTOMER, "timestamp", True, "Record creation time", read_only=True),
    FieldDefinition("updated_at", FieldCategory.CUSTOMER, "timestamp", True, "Last update", read_only=True),
)

# --- Section 6: Geographic ---
GEOGRAPHIC_FIELDS: tuple[FieldDefinition, ...] = (
    FieldDefinition("state", FieldCategory.GEOGRAPHIC, "string", True, "State abbreviation"),
    FieldDefinition("city", FieldCategory.GEOGRAPHIC, "string", False, "City"),
    FieldDefinition("county", FieldCategory.GEOGRAPHIC, "string", False, "County"),
    FieldDefinition("zip_code", FieldCategory.GEOGRAPHIC, "string", True, "Normalized ZIP", "zip"),
    FieldDefinition("zip_plus4", FieldCategory.GEOGRAPHIC, "string", False, "ZIP+4"),
    FieldDefinition("latitude", FieldCategory.GEOGRAPHIC, "decimal", False, "Latitude"),
    FieldDefinition("longitude", FieldCategory.GEOGRAPHIC, "decimal", False, "Longitude"),
    FieldDefinition("address", FieldCategory.GEOGRAPHIC, "string", False, "Street address"),
    FieldDefinition("country", FieldCategory.GEOGRAPHIC, "string", False, "Country"),
    FieldDefinition("contact_permission", FieldCategory.GEOGRAPHIC, "string", False, "Contact permission", "permission"),
)

# --- Section 6b: SFMC audience segmentation (upload source metadata) ---
AUDIENCE_SEGMENT_FIELDS: tuple[FieldDefinition, ...] = (
    FieldDefinition("segment_id", FieldCategory.CAMPAIGN, "string", False, "SFMC Segment ID", "sfmc_segment_id"),
    FieldDefinition("segment_code", FieldCategory.CAMPAIGN, "string", False, "SFMC Segment Code", "sfmc_segment_code"),
    FieldDefinition("segment_name", FieldCategory.CAMPAIGN, "string", False, "SFMC Segment Name", "sfmc_segment_name"),
    FieldDefinition("audience_segment", FieldCategory.CAMPAIGN, "string", False, "CIOS audience segment key", read_only=True),
)

# --- Section 7: Datalogix (values preserved unchanged) ---
DATALOGIX_FIELDS: tuple[FieldDefinition, ...] = (
    FieldDefinition("gender", FieldCategory.DATALOGIX, "string", False, "Gender"),
    FieldDefinition("age_range", FieldCategory.DATALOGIX, "string", False, "Age Range"),
    FieldDefinition("generation", FieldCategory.DATALOGIX, "string", False, "Generation"),
    FieldDefinition("adults", FieldCategory.DATALOGIX, "string", False, "Adults"),
    FieldDefinition("children", FieldCategory.DATALOGIX, "string", False, "Children"),
    FieldDefinition("persons", FieldCategory.DATALOGIX, "string", False, "Household Persons"),
    FieldDefinition("household_composition", FieldCategory.DATALOGIX, "string", False, "Household Composition", "household"),
    FieldDefinition("estimated_income", FieldCategory.DATALOGIX, "string", False, "Datalogix Estimated Income"),
    FieldDefinition("home_value", FieldCategory.DATALOGIX, "string", False, "Datalogix Home Value"),
    FieldDefinition("net_worth_indicator", FieldCategory.DATALOGIX, "string", False, "Net Worth Indicator", "net_worth"),
    FieldDefinition("dwelling_type", FieldCategory.DATALOGIX, "string", False, "Dwelling Type", "dwelling"),
    FieldDefinition("length_of_residence", FieldCategory.DATALOGIX, "string", False, "Length of Residence"),
    FieldDefinition("online_access", FieldCategory.DATALOGIX, "string", False, "Online Access"),
    FieldDefinition("retail_card", FieldCategory.DATALOGIX, "string", False, "Retail Card"),
    FieldDefinition("bank_card", FieldCategory.DATALOGIX, "string", False, "Bank Card"),
    FieldDefinition("dma_code", FieldCategory.DATALOGIX, "string", False, "Nielsen DMA Code"),
    FieldDefinition("county_code", FieldCategory.DATALOGIX, "string", False, "Datalogix County Code"),
)

# --- Section 8: ZIP Intelligence ---
ZIP_INTELLIGENCE_FIELDS: tuple[FieldDefinition, ...] = (
    FieldDefinition("median_income", FieldCategory.ZIP_INTELLIGENCE, "decimal", False, "ZIP Median Income"),
    FieldDefinition("top_50_income_zip", FieldCategory.ZIP_INTELLIGENCE, "boolean", False, "Premium ZIP Indicator", "top50_rank"),
    FieldDefinition("population", FieldCategory.ZIP_INTELLIGENCE, "integer", False, "Population"),
    FieldDefinition("zip_rank", FieldCategory.ZIP_INTELLIGENCE, "integer", False, "Income Rank"),
    FieldDefinition("county_name", FieldCategory.ZIP_INTELLIGENCE, "string", False, "County Name", "county"),
)

# --- Section 9: PRIZM Proxy ---
PRIZM_PROXY_VALUES: frozenset[str] = frozenset({
    "Established Elite",
    "Suburban Sophisticates",
    "Booming with Confidence",
    "Kids and Cul-de-Sacs",
    "Wellness Seekers",
    "Aging in Place",
    "Caregiving Households",
    "Simple Life",
    "Unknown",
})

PRIZM_FIELDS: tuple[FieldDefinition, ...] = (
    FieldDefinition("prizm_proxy_segment", FieldCategory.INTELLIGENCE, "enum", False, "PRIZM Proxy Segment", read_only=True),
    FieldDefinition("prizm_confidence", FieldCategory.INTELLIGENCE, "decimal", False, "PRIZM confidence", read_only=True),
)

# --- Section 10: Ceragem Intelligence ---
INTELLIGENCE_FIELDS: tuple[FieldDefinition, ...] = (
    FieldDefinition("ceragem_segment", FieldCategory.INTELLIGENCE, "enum", False, "Ceragem Segment", read_only=True),
    FieldDefinition("purchase_power", FieldCategory.INTELLIGENCE, "enum", False, "Purchase Power", "purchase_power_index", read_only=True),
    FieldDefinition("pain_index", FieldCategory.INTELLIGENCE, "enum", False, "Pain Index", read_only=True),
    FieldDefinition("lifestyle_index", FieldCategory.INTELLIGENCE, "enum", False, "Lifestyle Index", read_only=True),
    FieldDefinition("message_direction", FieldCategory.INTELLIGENCE, "enum", False, "Message Direction", read_only=True),
    FieldDefinition("campaign_priority", FieldCategory.INTELLIGENCE, "enum", False, "Campaign Priority", read_only=True),
    FieldDefinition("recommended_product", FieldCategory.INTELLIGENCE, "enum", False, "Recommended Product", read_only=True),
    FieldDefinition("expected_conversion", FieldCategory.INTELLIGENCE, "decimal", False, "Expected conversion", read_only=True),
    FieldDefinition("expected_revenue", FieldCategory.INTELLIGENCE, "currency", False, "Expected revenue", read_only=True),
)

# --- Section 11: Forecast ---
FORECAST_FIELDS: tuple[FieldDefinition, ...] = (
    FieldDefinition("target_customers", FieldCategory.FORECAST, "integer", False, "Forecast audience"),
    FieldDefinition("expected_orders", FieldCategory.FORECAST, "decimal", False, "Forecast orders"),
    FieldDefinition("expected_conversion_rate", FieldCategory.FORECAST, "decimal", False, "Conversion rate"),
    FieldDefinition("expected_revenue", FieldCategory.FORECAST, "currency", False, "Revenue"),
    FieldDefinition("expected_roi", FieldCategory.FORECAST, "decimal", False, "ROI"),
    FieldDefinition("expected_cpc", FieldCategory.FORECAST, "decimal", False, "CPC"),
    FieldDefinition("expected_cpa", FieldCategory.FORECAST, "decimal", False, "CPA"),
    FieldDefinition("expected_incentive", FieldCategory.FORECAST, "currency", False, "Le Frame Incentive"),
)

# --- Section 12: Campaign ---
CAMPAIGN_FIELDS: tuple[FieldDefinition, ...] = (
    FieldDefinition("campaign_id", FieldCategory.CAMPAIGN, "string", True, "Campaign Identifier"),
    FieldDefinition("campaign_name", FieldCategory.CAMPAIGN, "string", True, "Campaign Name"),
    FieldDefinition("campaign_type", FieldCategory.CAMPAIGN, "string", False, "Campaign Type"),
    FieldDefinition("campaign_status", FieldCategory.CAMPAIGN, "string", False, "Campaign Status", "status"),
    FieldDefinition("campaign_owner", FieldCategory.CAMPAIGN, "string", False, "Campaign Owner", "owner"),
    FieldDefinition("provider", FieldCategory.CAMPAIGN, "string", False, "Email Provider"),
    FieldDefinition("budget", FieldCategory.CAMPAIGN, "decimal", False, "Campaign Budget"),
    FieldDefinition("start_date", FieldCategory.CAMPAIGN, "date", False, "Start Date"),
    FieldDefinition("end_date", FieldCategory.CAMPAIGN, "date", False, "End Date"),
)

# --- Section 13: Campaign Performance ---
PERFORMANCE_FIELDS: tuple[FieldDefinition, ...] = (
    FieldDefinition("total_sent", FieldCategory.PERFORMANCE, "integer", False, "Sent", "sent"),
    FieldDefinition("delivered", FieldCategory.PERFORMANCE, "integer", False, "Delivered"),
    FieldDefinition("opened", FieldCategory.PERFORMANCE, "integer", False, "Open", "open"),
    FieldDefinition("unique_open", FieldCategory.PERFORMANCE, "integer", False, "Unique Open"),
    FieldDefinition("clicked", FieldCategory.PERFORMANCE, "integer", False, "Click", "click"),
    FieldDefinition("unique_click", FieldCategory.PERFORMANCE, "integer", False, "Unique Click", "unique_click"),
    FieldDefinition("ctr", FieldCategory.PERFORMANCE, "decimal", False, "Click Through Rate"),
    FieldDefinition("ctor", FieldCategory.PERFORMANCE, "decimal", False, "Click To Open Rate"),
    FieldDefinition("bounce", FieldCategory.PERFORMANCE, "integer", False, "Bounce"),
    FieldDefinition("unsubscribe", FieldCategory.PERFORMANCE, "integer", False, "Unsubscribe"),
    FieldDefinition("spam", FieldCategory.PERFORMANCE, "integer", False, "Spam Complaint"),
    FieldDefinition("actual_orders", FieldCategory.PERFORMANCE, "decimal", False, "Actual Orders"),
    FieldDefinition("actual_revenue", FieldCategory.PERFORMANCE, "currency", False, "Actual Revenue", "revenue"),
    FieldDefinition("cost", FieldCategory.PERFORMANCE, "currency", False, "Campaign cost"),
    FieldDefinition("roi", FieldCategory.PERFORMANCE, "decimal", False, "Return on investment"),
)

# --- Section 14: Learning ---
LEARNING_FIELDS: tuple[FieldDefinition, ...] = (
    FieldDefinition("learning_id", FieldCategory.LEARNING, "uuid", True, "Learning Identifier", "learning_id"),
    FieldDefinition("learning_score", FieldCategory.LEARNING, "decimal", False, "Learning Score"),
    FieldDefinition("forecast_accuracy", FieldCategory.LEARNING, "decimal", False, "Forecast Accuracy"),
    FieldDefinition("recommendation_accuracy", FieldCategory.LEARNING, "decimal", False, "Recommendation Accuracy"),
    FieldDefinition("created_campaign", FieldCategory.LEARNING, "string", False, "Source Campaign", "campaign_id"),
    FieldDefinition("learning_date", FieldCategory.LEARNING, "date", False, "Learning Date", "created_at"),
)

ALL_FIELDS: tuple[FieldDefinition, ...] = tuple(
    {f.name: f for f in (
        CUSTOMER_FIELDS
        + GEOGRAPHIC_FIELDS
        + DATALOGIX_FIELDS
        + ZIP_INTELLIGENCE_FIELDS
        + PRIZM_FIELDS
        + INTELLIGENCE_FIELDS
        + FORECAST_FIELDS
        + CAMPAIGN_FIELDS
        + AUDIENCE_SEGMENT_FIELDS
        + PERFORMANCE_FIELDS
        + LEARNING_FIELDS
    )}.values()
)

FIELD_REGISTRY: dict[str, FieldDefinition] = {f.name: f for f in ALL_FIELDS}

DICTIONARY_VERSION = "1.0"

# --- Section 15–16: Upload source → internal field (seeded to field_mapping table) ---
UPLOAD_SOURCE_MAPPINGS: list[tuple[str, str, str, bool]] = [
    ("Email Address", "email_address", "string", True),
    ("EMAIL", "email_address", "string", True),
    ("Email", "email_address", "string", True),
    ("email", "email_address", "string", True),
    ("email address", "email_address", "string", True),
    ("email_address", "email_address", "string", True),
    ("e-mail", "email_address", "string", True),
    ("First Name", "first_name", "string", False),
    ("first name", "first_name", "string", False),
    ("firstname", "first_name", "string", False),
    ("Last Name", "last_name", "string", False),
    ("last name", "last_name", "string", False),
    ("lastname", "last_name", "string", False),
    ("Phone", "phone", "string", False),
    ("phone", "phone", "string", False),
    ("Mobile Phone", "phone", "string", False),
    ("Address", "address", "string", False),
    ("address", "address", "string", False),
    ("City", "city", "string", False),
    ("city", "city", "string", False),
    ("State", "state", "string", False),
    ("state", "state", "string", False),
    ("ST", "state", "string", False),
    ("ZIP", "zip_code", "string", False),
    ("ZIP.1", "zip_code", "string", False),
    ("zip", "zip_code", "string", False),
    ("Zip Code", "zip_code", "string", False),
    ("zip code", "zip_code", "string", False),
    ("postal code", "zip_code", "string", False),
    ("Country", "country", "string", False),
    ("Contact Permission", "contact_permission", "string", False),
    ("permission", "contact_permission", "string", False),
    ("opt in", "contact_permission", "string", False),
    ("Segment ID", "segment_id", "string", False),
    ("Segment Code", "segment_code", "string", False),
    ("Segment Name", "segment_name", "string", False),
    ("Age Range", "age_range", "string", False),
    ("Generation", "generation", "string", False),
    ("Gender", "gender", "string", False),
    ("Estimated Income", "estimated_income", "string", False),
    ("estimated income", "estimated_income", "string", False),
    ("Home Value", "home_value", "string", False),
    ("Household Composition", "household_composition", "string", False),
    ("Household", "household_composition", "string", False),
    ("Length of Residence", "length_of_residence", "string", False),
    ("Net Worth", "net_worth_indicator", "string", False),
    ("Net Worth Indicator", "net_worth_indicator", "string", False),
    ("Online Access", "online_access", "string", False),
    ("Retail Card", "retail_card", "string", False),
    ("Dwelling Type", "dwelling_type", "string", False),
    ("Bank Card", "bank_card", "string", False),
    ("Adults in Household", "adults", "string", False),
    ("adults", "adults", "string", False),
    ("Children in Household", "children", "string", False),
    ("children", "children", "string", False),
    ("Persons in Household", "persons", "string", False),
    ("Number of Adults in Household", "adults", "string", False),
    ("Number of Children in Household", "children", "string", False),
    ("Number of Persons in Household", "persons", "string", False),
    # Ceragem SFMC exports — explicit Datalogix-prefixed headers (belt-and-suspenders with vendor-prefix strip).
    ("Datalogix - Age Range", "age_range", "string", False),
    ("Datalogix - Bank Card", "bank_card", "string", False),
    ("Datalogix - Dwelling Type", "dwelling_type", "string", False),
    ("Datalogix - Estimated Income", "estimated_income", "string", False),
    ("Datalogix - Gender", "gender", "string", False),
    ("Datalogix - Generation", "generation", "string", False),
    ("Datalogix - Home Value", "home_value", "string", False),
    ("Datalogix - Household Composition", "household_composition", "string", False),
    ("Datalogix - Length of Residence", "length_of_residence", "string", False),
    ("Datalogix - Net Worth Indicator", "net_worth_indicator", "string", False),
    ("Datalogix - Number of Adults in Household", "adults", "string", False),
    ("Datalogix - Number of Children in Household", "children", "string", False),
    ("Datalogix - Number of Persons in Household", "persons", "string", False),
    ("Datalogix - Online Access", "online_access", "string", False),
    ("Datalogix - Retail Card", "retail_card", "string", False),
    ("Datalogix - DMA Code", "dma_code", "string", False),
    ("Datalogix - County Code", "county_code", "string", False),
    ("DMA Code", "dma_code", "string", False),
    ("County Code", "county_code", "string", False),
]

REQUIRED_UPLOAD_FIELDS: frozenset[str] = frozenset({"email_address"})
RECOMMENDED_UPLOAD_FIELDS: frozenset[str] = frozenset({"state", "zip_code"})

# --- Section 19: Export internal → provider column labels ---
EXPORT_PROVIDER_MAPPINGS: list[tuple[str, str, str, int, bool]] = [
    ("Generic CSV", "email_address", "Email Address", 1, True),
    ("Generic CSV", "first_name", "First Name", 2, False),
    ("Generic CSV", "last_name", "Last Name", 3, False),
    ("Generic CSV", "phone", "Phone", 4, False),
    ("Generic CSV", "city", "City", 5, False),
    ("Generic CSV", "state", "State", 6, False),
    ("Generic CSV", "zip_code", "ZIP", 7, False),
    ("Generic CSV", "contact_permission", "Contact Permission", 8, False),
    ("Mailchimp", "email_address", "EMAIL", 1, True),
    ("Mailchimp", "first_name", "FNAME", 2, False),
    ("Mailchimp", "last_name", "LNAME", 3, False),
    ("Mailchimp", "zip_code", "ZIP", 4, False),
    ("HubSpot", "email_address", "email", 1, True),
    ("HubSpot", "first_name", "firstname", 2, False),
    ("HubSpot", "last_name", "lastname", 3, False),
    ("HubSpot", "zip_code", "Zip", 4, False),
    ("Klaviyo", "email_address", "email", 1, True),
    ("Klaviyo", "first_name", "first_name", 2, False),
    ("Klaviyo", "last_name", "last_name", 3, False),
    ("Attentive", "email_address", "email", 1, True),
    ("Attentive", "phone", "phone", 2, False),
    ("Salesforce Marketing Cloud", "email_address", "EmailAddress", 1, True),
    ("Salesforce Marketing Cloud", "first_name", "FirstName", 2, False),
    ("Salesforce Marketing Cloud", "last_name", "LastName", 3, False),
]

INTELLIGENCE_EXPORT_FIELDS: list[tuple[str, str]] = [
    ("prizm_proxy_segment", "PRIZM Proxy Segment"),
    ("ceragem_segment", "Ceragem Segment"),
    ("message_direction", "Message Direction"),
    ("recommended_product", "Recommended Product"),
    ("promo_code", "Promo Code"),
    ("recommended_promotion", "Recommended Promotion"),
    ("price_resistance_score", "Price Resistance Score"),
    ("commercial_version", "Commercial Version"),
]

# --- Section 20: Campaign report provider → internal ---
CAMPAIGN_REPORT_ALIASES: dict[str, list[str]] = {
    "campaign_id": ["campaign id", "campaign_id", "campaignid", "id"],
    "campaign_name": ["campaign name", "campaign_name", "campaign", "name"],
    "campaign_type": ["campaign type", "campaign_type", "type"],
    "state": ["state", "st", "state code"],
    "total_sent": ["sent", "emails sent", "total sent"],
    "delivered": ["delivered", "emails delivered"],
    "opened": ["open", "opens", "total open", "unique opens"],
    "clicked": ["click", "clicks", "total click", "total clicks"],
    "unique_click": ["unique click", "unique_click", "unique clicks"],
    "open_rate": ["open rate", "open_rate", "open %"],
    "ctr": ["ctr", "click rate", "click_rate", "click-through rate"],
    "ctor": ["ctor", "click to open", "click-to-open"],
    "cost": ["cost", "spend", "total cost", "campaign cost"],
    "cpc": ["cpc", "cost per click"],
    "actual_revenue": ["revenue", "sales", "total revenue"],
    "roi": ["roi", "return on investment"],
    "category": ["category", "click category", "link category"],
    "product": ["product", "product click", "product name"],
    "click_count": ["click count", "click_count", "clicks"],
    "click_rate": ["click rate category", "category click rate"],
}

# --- Section 18: Dashboard metric mapping ---
DASHBOARD_METRIC_MAP: dict[str, str] = {
    "target_customers": "target_customers",
    "total_customers": "target_customers",
    "expected_revenue": "expected_revenue",
    "campaign_roi": "expected_roi",
    "le_frame_incentive": "expected_incentive",
    "state": "state",
    "zip_code": "zip_code",
    "recommended_product": "recommended_product",
}


def resolve_column(column_map: dict[str, str | None], internal_field: str) -> str | None:
    """Resolve upload column header for an internal field (supports legacy map keys)."""
    if column_map.get(internal_field):
        return column_map[internal_field]
    legacy = db_column(internal_field)
    if legacy != internal_field:
        return column_map.get(legacy)
    return None


def detect_duplicate_source_mappings(column_map: dict[str, str | None]) -> list[str]:
    """Section 15 — duplicate source headers mapped to multiple internal fields."""
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for internal, source in column_map.items():
        if not source:
            continue
        if source in seen:
            prior = seen[source]
            if prior != internal and db_column(prior) != internal and db_column(internal) != prior:
                if source not in duplicates:
                    duplicates.append(source)
        else:
            seen[source] = internal
    return duplicates


# Fields written to Customer ORM on upload (subset of customer + geographic)
CUSTOMER_UPLOAD_FIELDS: tuple[str, ...] = (
    "email_address",
    "first_name",
    "last_name",
    "phone",
    "address",
    "city",
    "state",
    "zip_code",
    "country",
    "contact_permission",
    "segment_id",
    "segment_code",
    "segment_name",
)


def customer_internal_fields() -> list[str]:
    return list(CUSTOMER_UPLOAD_FIELDS)


def datalogix_internal_fields() -> list[str]:
    return [f.name for f in DATALOGIX_FIELDS]


def apply_internal_to_model_data(internal_data: dict[str, str | None]) -> dict[str, str | None]:
    """Map internal field names to database column names for ORM writes."""
    return {db_column(k): v for k, v in internal_data.items()}


def export_field_value(internal_field: str, customer, intelligence) -> str:
    """Resolve export value from customer/intelligence ORM objects."""
    col = db_column(internal_field)
    if internal_field.startswith("intel_") or internal_field in {f[0] for f in INTELLIGENCE_EXPORT_FIELDS}:
        intel_field = internal_field.replace("intel_", "")
        return str(getattr(intelligence, intel_field, None) or "")
    if hasattr(customer, col):
        return str(getattr(customer, col, None) or "")
    return ""


EXPORT_VALUE_RESOLVERS: dict[str, Callable] = {
    "email_address": lambda c, i: c.email or "",
    "first_name": lambda c, i: c.first_name or "",
    "last_name": lambda c, i: c.last_name or "",
    "phone": lambda c, i: c.phone or "",
    "address": lambda c, i: c.address or "",
    "city": lambda c, i: c.city or "",
    "state": lambda c, i: c.state or "",
    "zip_code": lambda c, i: c.zip or "",
    "contact_permission": lambda c, i: c.permission or "",
    "intel_prizm_proxy_segment": lambda c, i: i.prizm_proxy_segment or "",
    "intel_ceragem_segment": lambda c, i: i.ceragem_segment or "",
    "intel_message_direction": lambda c, i: i.message_direction or "",
    "intel_recommended_product": lambda c, i: i.recommended_product or "",
}
