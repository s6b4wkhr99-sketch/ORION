"""Volume 22 — Reference Data Library registry and seed definitions (SSOT)."""

RDL_VERSION = "Volume 22 v1.0"
RDL_OWNER = "Ceragem CIOS Data Governance"

REFERENCE_DOMAINS: tuple[dict, ...] = (
    {"domain": "geographic", "tables": ("state_master", "county_master", "zip_master", "time_zone_master", "country_master")},
    {"domain": "customer", "tables": ("gender_master", "generation_master", "household_master", "dwelling_master", "income_range_master")},
    {"domain": "product", "tables": ("product_master",)},
    {"domain": "campaign", "tables": ("campaign_type_master", "campaign_status_master", "message_type_master", "holiday_master")},
    {"domain": "intelligence", "tables": ("purchase_power_master", "pain_index_master", "lifestyle_master", "ceragem_segment_master", "priority_master")},
    {"domain": "provider", "tables": ("provider_master", "provider_version_master", "provider_status_master")},
    {"domain": "dashboard", "tables": ("dashboard_master", "metric_master", "chart_type_master")},
    {"domain": "system", "tables": ("role_master", "permission_master", "language_master", "currency_master", "status_master")},
)

GOVERNANCE_FIELDS: tuple[str, ...] = (
    "reference_version",
    "created_date",
    "modified_date",
    "owner",
    "approval_status",
)

RDL_ACCEPTANCE_CRITERIA: tuple[dict, ...] = (
    {"id": "RDL-01", "criterion": "All standardized values originate from reference tables"},
    {"id": "RDL-02", "criterion": "No hard-coded reference values in business logic"},
    {"id": "RDL-03", "criterion": "Every module consumes centralized reference data"},
    {"id": "RDL-04", "criterion": "Reference data is version controlled"},
    {"id": "RDL-05", "criterion": "Product additions require no source code modification"},
    {"id": "RDL-06", "criterion": "Dashboard configuration is metadata driven"},
    {"id": "RDL-07", "criterion": "Intelligence values are standardized"},
    {"id": "RDL-08", "criterion": "Campaign values are standardized"},
    {"id": "RDL-09", "criterion": "Geographic enrichment is centralized"},
)

# --- Geographic ---
US_STATES: list[tuple[str, str, str, str]] = [
    ("AL", "Alabama", "South", "Central"),
    ("AK", "Alaska", "West", "Alaska"),
    ("AZ", "Arizona", "West", "Mountain"),
    ("AR", "Arkansas", "South", "Central"),
    ("CA", "California", "West", "Pacific"),
    ("CO", "Colorado", "West", "Mountain"),
    ("CT", "Connecticut", "Northeast", "Eastern"),
    ("DE", "Delaware", "Northeast", "Eastern"),
    ("FL", "Florida", "South", "Eastern"),
    ("GA", "Georgia", "South", "Eastern"),
    ("HI", "Hawaii", "West", "Hawaii-Aleutian"),
    ("ID", "Idaho", "West", "Mountain"),
    ("IL", "Illinois", "Midwest", "Central"),
    ("IN", "Indiana", "Midwest", "Eastern"),
    ("IA", "Iowa", "Midwest", "Central"),
    ("KS", "Kansas", "Midwest", "Central"),
    ("KY", "Kentucky", "South", "Eastern"),
    ("LA", "Louisiana", "South", "Central"),
    ("ME", "Maine", "Northeast", "Eastern"),
    ("MD", "Maryland", "Northeast", "Eastern"),
    ("MA", "Massachusetts", "Northeast", "Eastern"),
    ("MI", "Michigan", "Midwest", "Eastern"),
    ("MN", "Minnesota", "Midwest", "Central"),
    ("MS", "Mississippi", "South", "Central"),
    ("MO", "Missouri", "Midwest", "Central"),
    ("MT", "Montana", "West", "Mountain"),
    ("NE", "Nebraska", "Midwest", "Central"),
    ("NV", "Nevada", "West", "Pacific"),
    ("NH", "New Hampshire", "Northeast", "Eastern"),
    ("NJ", "New Jersey", "Northeast", "Eastern"),
    ("NM", "New Mexico", "West", "Mountain"),
    ("NY", "New York", "Northeast", "Eastern"),
    ("NC", "North Carolina", "South", "Eastern"),
    ("ND", "North Dakota", "Midwest", "Central"),
    ("OH", "Ohio", "Midwest", "Eastern"),
    ("OK", "Oklahoma", "South", "Central"),
    ("OR", "Oregon", "West", "Pacific"),
    ("PA", "Pennsylvania", "Northeast", "Eastern"),
    ("RI", "Rhode Island", "Northeast", "Eastern"),
    ("SC", "South Carolina", "South", "Eastern"),
    ("SD", "South Dakota", "Midwest", "Central"),
    ("TN", "Tennessee", "South", "Central"),
    ("TX", "Texas", "South", "Central"),
    ("UT", "Utah", "West", "Mountain"),
    ("VT", "Vermont", "Northeast", "Eastern"),
    ("VA", "Virginia", "South", "Eastern"),
    ("WA", "Washington", "West", "Pacific"),
    ("WV", "West Virginia", "South", "Eastern"),
    ("WI", "Wisconsin", "Midwest", "Central"),
    ("WY", "Wyoming", "West", "Mountain"),
    ("DC", "District of Columbia", "Northeast", "Eastern"),
]

COUNTRIES: list[tuple[str, str]] = [("US", "United States")]

TIME_ZONES: list[tuple[str, str]] = [
    ("Eastern", "America/New_York"),
    ("Central", "America/Chicago"),
    ("Mountain", "America/Denver"),
    ("Pacific", "America/Los_Angeles"),
    ("Alaska", "America/Anchorage"),
    ("Hawaii-Aleutian", "Pacific/Honolulu"),
]

# --- Customer reference ---
GENDER_VALUES: list[tuple[str, str, int]] = [
    ("Male", "Male", 1),
    ("Female", "Female", 2),
    ("Unknown", "Unknown", 3),
]

GENERATION_VALUES: list[tuple[str, str, int]] = [
    ("Gen Z", "Generation Z", 1),
    ("Millennial", "Millennial", 2),
    ("Gen X", "Generation X", 3),
    ("Baby Boomer", "Baby Boomer", 4),
    ("Silent", "Silent Generation", 5),
    ("Unknown", "Unknown", 6),
]

HOUSEHOLD_VALUES: list[tuple[str, str, int]] = [
    ("1", "Single Person", 1),
    ("2", "Couple", 2),
    ("3+", "Family", 3),
    ("Unknown", "Unknown", 4),
]

DWELLING_VALUES: list[tuple[str, str, int]] = [
    ("Single Family", "Single Family Home", 1),
    ("Multi Family", "Multi Family", 2),
    ("Condo", "Condominium", 3),
    ("Unknown", "Unknown", 4),
]

INCOME_RANGE_VALUES: list[tuple[str, str, int]] = [
    ("X", "High Income", 1),
    ("Y", "Medium Income", 2),
    ("Z", "Lower Income", 3),
    ("U", "Unknown", 4),
]

# ORION Commercial Intelligence — Version 2026.07 (Production Business Rules)
COMMERCIAL_VERSION = "2026.07"

# --- Product ---
PRODUCT_CATALOG: list[dict] = [
    {
        "code": "Master V9",
        "name": "Master V9",
        "family": "Master",
        "category": "Premium",
        "msrp": 9999.0,
        "selling_price": 8199.0,
        "max_promotion": 1800.0,
        "gross_sales": 8199.0,
        "ceragem_cogs": 3820.0,
        "default_promotion_pct": None,
        "promo_code": None,
        "le_frame_incentive": 1499.85,
        "segment": "Premium Wellness",
        "order": 1,
        "active": True,
    },
    {
        "code": "Master V7",
        "name": "Master V7",
        "family": "Master",
        "category": "Premium",
        "msrp": 8499.0,
        "selling_price": 6999.0,
        "max_promotion": 1500.0,
        "gross_sales": 6999.0,
        "ceragem_cogs": 3038.0,
        "default_promotion_pct": None,
        "promo_code": None,
        "le_frame_incentive": 1049.85,
        "segment": "Therapeutic Wellness",
        "order": 2,
        "active": True,
    },
    {
        "code": "Master V6",
        "name": "Master V6",
        "family": "Master",
        "category": "Core",
        "msrp": 7999.0,
        "selling_price": 6399.0,
        "max_promotion": 1600.0,
        "gross_sales": 6399.0,
        "ceragem_cogs": 2980.0,
        "default_promotion_pct": 0.20,
        "promo_code": "SAVE20",
        "le_frame_incentive": 959.85,
        "segment": "Lifestyle Wellness",
        "order": 3,
        "active": True,
    },
    {
        "code": "Master V5",
        "name": "Master V5",
        "family": "Master",
        "category": "Core",
        "msrp": 5999.0,
        "selling_price": 4799.0,
        "max_promotion": 1200.0,
        "gross_sales": 4799.0,
        "ceragem_cogs": 2348.0,
        "default_promotion_pct": 0.20,
        "promo_code": "SAVE20",
        "le_frame_incentive": 719.85,
        "segment": "Lifestyle Wellness",
        "order": 4,
        "active": True,
    },
    {
        "code": "Master S4",
        "name": "Master S4",
        "family": "Master",
        "category": "Core",
        "msrp": 5499.0,
        "selling_price": 5499.0,
        "max_promotion": 1650.0,
        "gross_sales": 5499.0,
        "ceragem_cogs": 2125.0,
        "default_promotion_pct": 0.30,
        "promo_code": "SAVE30",
        "le_frame_incentive": 824.85,
        "segment": "Emerging Wellness",
        "order": 5,
        "active": True,
    },
    {
        "code": "Pause M10",
        "name": "Pause M10",
        "family": "Pause",
        "category": "Massage",
        "msrp": 13999.0,
        "selling_price": 9799.0,
        "max_promotion": 4200.0,
        "gross_sales": 9799.0,
        "ceragem_cogs": 3150.0,
        "default_promotion_pct": 0.30,
        "promo_code": "SAVE30",
        "le_frame_incentive": 1469.85,
        "segment": "Premium Wellness",
        "order": 7,
        "active": True,
    },
    {
        "code": "Pause M6",
        "name": "Pause M6",
        "family": "Pause",
        "category": "Massage",
        "msrp": 6499.0,
        "selling_price": 4999.0,
        "max_promotion": 1500.0,
        "gross_sales": 4999.0,
        "ceragem_cogs": 2218.0,
        "default_promotion_pct": None,
        "promo_code": None,
        "le_frame_incentive": 749.85,
        "segment": "Family Wellness",
        "order": 8,
        "active": True,
    },
    {
        "code": "Pause M6s",
        "name": "Pause M6s",
        "family": "Pause",
        "category": "Massage",
        "msrp": 5999.0,
        "selling_price": 4799.0,
        "max_promotion": 1200.0,
        "gross_sales": 4799.0,
        "ceragem_cogs": 2000.0,
        "default_promotion_pct": 0.20,
        "promo_code": "SAVE20",
        "le_frame_incentive": 749.85,
        "segment": "Family Wellness",
        "order": 9,
        "active": True,
    },
    {
        "code": "Pause M4",
        "name": "Pause M4",
        "family": "Pause",
        "category": "Massage",
        "msrp": 4999.0,
        "selling_price": 3999.0,
        "max_promotion": 1000.0,
        "gross_sales": 3999.0,
        "ceragem_cogs": 1700.0,
        "default_promotion_pct": None,
        "promo_code": None,
        "le_frame_incentive": 599.85,
        "segment": "Family Wellness",
        "order": 10,
        "active": True,
    },
    {
        "code": "Pause M2",
        "name": "Pause M2",
        "family": "Pause",
        "category": "Massage",
        "msrp": 2999.0,
        "max_promotion": 0.0,
        "gross_sales": 2999.0,
        "le_frame_incentive": 450.0,
        "segment": "Opportunity",
        "order": 99,
        "active": False,
    },
    {
        "code": "MediSpa / Cellunic",
        "name": "MediSpa / Cellunic",
        "family": "MediSpa",
        "category": "Accessory",
        "msrp": 2499.0,
        "max_promotion": 0.0,
        "gross_sales": 2499.0,
        "le_frame_incentive": 375.0,
        "segment": "Opportunity",
        "order": 100,
        "active": False,
    },
]

# Default promotion operating plan (seed). Runtime active promos come from published catalog.
ACTIVE_STANDING_PROMOTIONS: dict[str, dict[str, object]] = {
    "Master V6": {"promo_code": "SAVE20", "default_promotion_pct": 0.20},
    "Master V5": {"promo_code": "SAVE20", "default_promotion_pct": 0.20},
    "Master S4": {"promo_code": "SAVE30", "default_promotion_pct": 0.30},
    "Pause M10": {"promo_code": "SAVE30", "default_promotion_pct": 0.30},
    "Pause M6s": {"promo_code": "SAVE20", "default_promotion_pct": 0.20},
}

ACTIVE_STANDING_PROMOTION_ORDER: tuple[str, ...] = (
    "Master V6",
    "Master V5",
    "Master S4",
    "Pause M10",
    "Pause M6s",
)

# Observed unit sales mix anchor — V Series (FDA Class 2 therapeutic) : M Series (design/sleep).
OBSERVED_V_M_SALES_MIX: tuple[float, float] = (0.65, 0.35)

FDA_CLASS_2_PRODUCTS: frozenset[str] = frozenset(
    {"Master S4", "Master V5", "Master V6", "Master V7", "Master V9"}
)

# Legacy SKU codes retained in historical uploads / intelligence_version snapshots.
# Legacy names — same physical SKU as Master S4 (formerly marketed as Pause S4).
LEGACY_PRODUCT_ALIASES: dict[str, str] = {
    "Master V4": "Master S4",
    "Pause S4": "Master S4",
}
V_SERIES_PRODUCTS: frozenset[str] = FDA_CLASS_2_PRODUCTS
M_SERIES_PRODUCTS: frozenset[str] = frozenset(
    {"Pause M4", "Pause M6", "Pause M6s", "Pause M10"}
)


def is_fda_class_2(product_code: str) -> bool:
    return product_code in FDA_CLASS_2_PRODUCTS


def product_line(product_code: str) -> str:
    product_code = LEGACY_PRODUCT_ALIASES.get(product_code, product_code)
    if product_code in V_SERIES_PRODUCTS:
        return "V"
    if product_code in M_SERIES_PRODUCTS:
        return "M"
    return "Other"


def normalize_product_code(product_code: str | None) -> str:
    code = (product_code or "").strip()
    return LEGACY_PRODUCT_ALIASES.get(code, code)


def has_standing_promotion(product_code: str) -> bool:
    return product_code in ACTIVE_STANDING_PROMOTIONS


# --- Campaign ---
CAMPAIGN_TYPES: list[tuple[str, str, int]] = [
    ("Technology", "Technology-focused campaign", 1),
    ("FDA Cleared", "FDA cleared product messaging", 2),
    ("Promotion", "Promotional offer campaign", 3),
    ("Lifestyle", "Lifestyle wellness campaign", 4),
    ("Financing", "Financing offer campaign", 5),
    ("Consultation", "Consultation invitation", 6),
    ("Education", "Product education campaign", 7),
    ("Holiday", "Holiday seasonal campaign", 8),
    ("Retention", "Customer retention campaign", 9),
    ("Win-back", "Win-back inactive customers", 10),
]

CAMPAIGN_STATUSES: list[tuple[str, str, int]] = [
    ("Draft", "Campaign draft", 1),
    ("Pending Approval", "Awaiting approval", 2),
    ("Approved", "Approved for execution", 3),
    ("Active", "Currently running", 4),
    ("Completed", "Campaign completed", 5),
    ("Cancelled", "Campaign cancelled", 6),
]

MESSAGE_TYPES: list[tuple[str, str, int]] = [
    ("Pain Relief", "Pain relief messaging", 1),
    ("FDA Cleared", "FDA cleared messaging", 2),
    ("Technology", "Technology messaging", 3),
    ("Lifestyle Wellness", "Lifestyle wellness messaging", 4),
    ("Luxury Wellness", "Luxury wellness messaging", 5),
    ("Family Wellness", "Family wellness messaging", 6),
    ("Consultation", "Consultation invitation", 7),
    ("Financing", "Financing offer", 8),
    ("Promotion", "Promotional messaging", 9),
]

HOLIDAYS: list[tuple[str, str, int]] = [
    ("New Year", "New Year promotion", 1),
    ("Valentine", "Valentine seasonal", 2),
    ("Mother's Day", "Mother's Day campaign", 3),
    ("Father's Day", "Father's Day campaign", 4),
    ("Black Friday", "Black Friday promotion", 5),
    ("Holiday Season", "Year-end holiday", 6),
]

# --- Intelligence ---
INDEX_LEVELS: list[tuple[str, str, str, float, int]] = [
    ("High", "High purchase power", "#16a34a", 0.85, 1),
    ("Medium", "Medium purchase power", "#ca8a04", 0.55, 2),
    ("Low", "Low purchase power", "#dc2626", 0.25, 3),
]

PAIN_INDEX_LEVELS: list[tuple[str, str, str, float, int]] = [
    ("High", "High pain index", "#dc2626", 0.75, 1),
    ("Medium", "Medium pain index", "#ca8a04", 0.50, 2),
    ("Low", "Low pain index", "#16a34a", 0.25, 3),
]

LIFESTYLE_LEVELS: list[tuple[str, str, float, int]] = [
    ("High", "High lifestyle orientation", 0.85, 1),
    ("Medium", "Medium lifestyle orientation", 0.55, 2),
    ("Low", "Low lifestyle orientation", 0.25, 3),
]

CERAGEM_SEGMENT_V19: list[tuple[str, str, str, int]] = [
    ("Premium Wellness", "Premium wellness segment", "High + Wellness", 1),
    ("Therapeutic Wellness", "Therapeutic focus segment", "High + Pain Index", 2),
    ("Lifestyle Wellness", "Lifestyle wellness segment", "Mid-High + Wellness", 3),
    ("Emerging Wellness", "Emerging opportunity segment", "Mid-Low + Wellness", 4),
    ("Family Wellness", "Family-oriented segment", "Mid-Low + Pain Index", 5),
    ("Opportunity", "Growth opportunity segment", "Low + Wellness", 6),
    ("Low Priority", "Low priority segment", "Low + Pain Index", 7),
    ("Unknown", "Unclassified segment", "Unknown", 8),
]

CERAGEM_V19_MAP: dict[str, str] = {
    "High+ · Wellness": "Premium Wellness",
    "High+ · Pain Index": "Therapeutic Wellness",
    "Mid-High+ · Wellness": "Lifestyle Wellness",
    "Mid-High+ · Pain Index": "Therapeutic Wellness",
    "Mid+ · Wellness": "Lifestyle Wellness",
    "Mid+ · Pain Index": "Family Wellness",
    "Mid-Low+ · Wellness": "Emerging Wellness",
    "Mid-Low+ · Pain Index": "Family Wellness",
    "Low+ · Wellness": "Opportunity",
    "Low+ · Pain Index": "Low Priority",
    # Legacy V04 labels (pre tier+ refactor)
    "High + Wellness": "Premium Wellness",
    "High + Pain Index": "Therapeutic Wellness",
    "Mid-High + Wellness": "Lifestyle Wellness",
    "Mid-High + Pain Index": "Therapeutic Wellness",
    "Mid-Low + Wellness": "Emerging Wellness",
    "Mid-Low + Pain Index": "Family Wellness",
    "Low + Wellness": "Opportunity",
    "Low + Pain Index": "Low Priority",
}

CERAGEM_SEGMENT_V04: list[str] = [
    "High+ · Wellness",
    "High+ · Pain Index",
    "Mid-High+ · Wellness",
    "Mid-High+ · Pain Index",
    "Mid+ · Wellness",
    "Mid+ · Pain Index",
    "Mid-Low+ · Wellness",
    "Mid-Low+ · Pain Index",
    "Low+ · Wellness",
    "Low+ · Pain Index",
]

PRIZM_SEGMENTS: list[tuple[str, str, int]] = [
    ("Established Elite", "Premium established households", 1),
    ("Suburban Sophisticates", "Affluent suburban households", 2),
    ("Booming with Confidence", "Growing affluent households", 3),
    ("Kids and Cul-de-Sacs", "Family suburban households", 4),
    ("Wellness Seekers", "Health and wellness focused", 5),
    ("Aging in Place", "Senior aging households", 6),
    ("Caregiving Households", "Caregiver households", 7),
    ("Simple Life", "Value-focused households", 8),
    ("Unknown", "Unclassified PRIZM proxy", 9),
]

PRIORITY_LEVELS: list[tuple[str, str, float, int]] = [
    ("High", "High campaign priority", 0.9, 1),
    ("Medium", "Medium campaign priority", 0.55, 2),
    ("Low", "Low campaign priority", 0.25, 3),
]

# --- Provider ---
PROVIDER_NAMES: list[tuple[str, str, int]] = [
    ("Generic CSV", "Generic CSV export/import", 1),
    ("Mailchimp", "Mailchimp ESP", 2),
    ("Klaviyo", "Klaviyo ESP", 3),
    ("HubSpot", "HubSpot Marketing", 4),
    ("Attentive", "Attentive SMS/MMS", 5),
    ("Salesforce Marketing Cloud", "SFMC", 6),
]

PROVIDER_STATUSES: list[tuple[str, str, int]] = [
    ("active", "Active provider integration", 1),
    ("deprecated", "Deprecated provider", 2),
    ("planned", "Planned integration", 3),
]

# --- Dashboard ---
DASHBOARD_DEFINITIONS: list[tuple[str, str, int]] = [
    ("executive", "Executive Dashboard", 1),
    ("customer", "Customer Intelligence Dashboard", 2),
    ("campaign", "Campaign Performance Dashboard", 3),
    ("state", "State Dashboard", 4),
    ("zip", "ZIP Dashboard", 5),
    ("product", "Product Dashboard", 6),
    ("roi", "ROI Dashboard", 7),
    ("export", "Export Center", 8),
]

METRIC_DEFINITIONS: list[tuple[str, str, str, int]] = [
    ("total_customers", "Total Customers", "count", 1),
    ("targetable_customers", "Targetable Customers", "count", 2),
    ("expected_revenue", "Expected Revenue", "currency", 3),
    ("expected_conversion", "Expected Conversion", "rate", 4),
    ("campaign_roi", "Campaign ROI", "percent", 5),
    ("open_rate", "Open Rate", "percent", 6),
    ("ctr", "Click-Through Rate", "percent", 7),
]

CHART_TYPES: list[tuple[str, str, int]] = [
    ("bar", "Bar Chart", 1),
    ("line", "Line Chart", 2),
    ("pie", "Pie Chart", 3),
    ("radar", "Radar Chart", 4),
    ("table", "Data Table", 5),
]

# --- System ---
LANGUAGES: list[tuple[str, str, int]] = [("en-US", "English (United States)", 1)]
CURRENCIES: list[tuple[str, str, str, int]] = [("USD", "US Dollar", "$", 1)]
SYSTEM_STATUSES: list[tuple[str, str, int]] = [
    ("active", "Active record", 1),
    ("inactive", "Inactive record", 2),
    ("pending", "Pending approval", 3),
]

# Convenience tuples for modules (derived from registry — not business logic)
PRODUCT_CODES: tuple[str, ...] = tuple(p["code"] for p in PRODUCT_CATALOG)
ACTIVE_PRODUCT_CODES: tuple[str, ...] = tuple(p["code"] for p in PRODUCT_CATALOG if p.get("active", True))
SUPPORTED_PRODUCTS: tuple[str, ...] = tuple(
    p["code"]
    for p in PRODUCT_CATALOG
    if p["family"] in {"Master", "Pause"} and p.get("active", True)
)
PURCHASE_POWER_LEVELS: tuple[str, ...] = tuple(x[0] for x in INDEX_LEVELS)
LEVEL_TO_INDEX: dict[str, float] = {x[0]: x[3] for x in INDEX_LEVELS}
PRODUCT_PRICES: dict[str, float] = {p["code"]: p["msrp"] for p in PRODUCT_CATALOG}
PRODUCT_GROSS_SALES: dict[str, float] = {p["code"]: p["gross_sales"] for p in PRODUCT_CATALOG}
PRODUCT_MAX_PROMOTION: dict[str, float] = {p["code"]: p["max_promotion"] for p in PRODUCT_CATALOG}
LE_FRAME_INCENTIVE_BY_SKU: dict[str, float] = {p["code"]: p["le_frame_incentive"] for p in PRODUCT_CATALOG}
PRODUCT_FORECAST_PRICES: dict[str, float] = PRODUCT_GROSS_SALES
LE_FRAME_COMMISSION_RATE = 0.15
