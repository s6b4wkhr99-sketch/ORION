"""RFC-001 — Auto Mapping Engine constants."""

RFC_VERSION = "RFC-001 v1.1"

MATCH_EXACT = "exact"
MATCH_ALIAS = "alias"
MATCH_PROVIDER_TEMPLATE = "provider_template"
MATCH_AI_SIMILARITY = "ai_similarity"
MATCH_UNKNOWN = "unknown"

CONFIDENCE_EXACT = 100
CONFIDENCE_ALIAS_MIN = 95
CONFIDENCE_ALIAS_MAX = 99
CONFIDENCE_PROVIDER_MIN = 90
CONFIDENCE_PROVIDER_MAX = 95
CONFIDENCE_AI_MIN = 80
CONFIDENCE_AI_MAX = 90
CONFIDENCE_REVIEW_THRESHOLD = 80

STATUS_MAPPED = "mapped"
STATUS_REVIEW = "review"
STATUS_IGNORED = "ignored"

PROVIDER_TEMPLATES: tuple[str, ...] = (
    "Customer Master",
    "Datalogix",
    "Mailchimp Export",
    "Klaviyo Export",
    "HubSpot Export",
    "Attentive Export",
    "Salesforce Marketing Cloud",
    "Generic CSV",
)

# Provider template header → internal field (upload direction)
PROVIDER_UPLOAD_HEADERS: dict[str, list[tuple[str, str]]] = {
    "Mailchimp Export": [
        ("email address", "email_address"),
        ("fname", "first_name"),
        ("lname", "last_name"),
        ("state", "state"),
        ("zip", "zip_code"),
    ],
    "Klaviyo Export": [
        ("email", "email_address"),
        ("first name", "first_name"),
        ("last name", "last_name"),
        ("state", "state"),
        ("zip", "zip_code"),
    ],
    "HubSpot Export": [
        ("email", "email_address"),
        ("firstname", "first_name"),
        ("lastname", "last_name"),
        ("state", "state"),
        ("zip", "zip_code"),
    ],
    "Generic CSV": [
        ("email", "email_address"),
        ("first name", "first_name"),
        ("last name", "last_name"),
        ("state", "state"),
        ("zip", "zip_code"),
    ],
}
