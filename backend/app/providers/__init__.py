"""Volume 15 — Provider integration package."""

from app.providers.constants import SUPPORTED_PROVIDERS
from app.providers.registry import detect_provider_from_headers, get_adapter

__all__ = ["SUPPORTED_PROVIDERS", "get_adapter", "detect_provider_from_headers"]
