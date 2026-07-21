"""Volume 15 Section 4 — Supported mass email providers (RDL-sourced)."""

from app.reference.registry import PROVIDER_NAMES

SUPPORTED_PROVIDERS: tuple[str, ...] = tuple(provider[0] for provider in PROVIDER_NAMES)

# Backward compatibility
EXPORT_PROVIDERS = SUPPORTED_PROVIDERS

PROVIDER_MAPPING_VERSION = "1.0.0"
COMPATIBILITY_VERSION = "CIOS 1.0"
