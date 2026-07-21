"""Volume 15 — Provider adapter registry."""

from app.providers.adapter import ADAPTER_CLASSES
from app.providers.base import ProviderAdapter
from app.providers.config import PROVIDER_IMPORT_SIGNATURES
from app.providers.constants import SUPPORTED_PROVIDERS
from app.providers.normalization import normalize_header


def get_adapter(provider_name: str) -> ProviderAdapter:
    if provider_name not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider_name}")
    cls = ADAPTER_CLASSES[provider_name]
    return cls()


def detect_provider_from_headers(headers: list[str]) -> str:
    """Section 6 — provider detection from report headers."""
    normalized = {normalize_header(h) for h in headers}
    best_name = "Generic CSV"
    best_score = 0
    for name in SUPPORTED_PROVIDERS:
        if name == "Generic CSV":
            continue
        sig = PROVIDER_IMPORT_SIGNATURES.get(name, set())
        score = len(normalized & sig)
        if score > best_score:
            best_score = score
            best_name = name
    if best_score >= 2:
        return best_name
    if "fname" in normalized or "email address" in normalized:
        return "Mailchimp"
    if "subscriberkey" in normalized or "emailaddress" in normalized:
        return "Salesforce Marketing Cloud"
    if "firstname" in normalized and "conversion" in normalized:
        return "HubSpot"
    if {"sent", "open", "click"} <= normalized:
        return "Mailchimp"
    if "delivered" in normalized and "opened" in normalized:
        return "Klaviyo"
    return "Generic CSV"
