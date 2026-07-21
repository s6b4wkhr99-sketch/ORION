"""Volume 18 — AI Recommendation Engine constants (sourced from RDL registry)."""

from app.reference.registry import (
    CAMPAIGN_TYPES as _CAMPAIGN_TYPE_SEED,
    MESSAGE_TYPES as _MESSAGE_TYPE_SEED,
    PRODUCT_CATALOG,
    SUPPORTED_PRODUCTS,
)

ENGINE_VERSION = "Volume 18 v1.0"
RULE_VERSION = "Volume 04 Rules 065–067"
LEARNING_VERSION = "Volume 06 Campaign Learning"

PRODUCTS = SUPPORTED_PRODUCTS
MESSAGE_TYPES = tuple(message[0] for message in _MESSAGE_TYPE_SEED)
CAMPAIGN_TYPES = tuple(campaign[0] for campaign in _CAMPAIGN_TYPE_SEED)

MESSAGE_DIRECTION_MAP = {
    "Pain Relief Message": "Pain Relief",
    "Product Education Message": "Technology",
    "Premium Wellness Message": "Luxury Wellness",
    "Financing Message": "Financing",
    "Consultation Message": "Consultation",
    "Family Wellness Message": "Family Wellness",
    "Promotion Message": "Promotion",
    "FDA Cleared Message": "FDA Cleared",
    "Lifestyle Wellness Message": "Lifestyle Wellness",
}

STRATEGY_TO_CAMPAIGN = {
    "Premium Campaign": "Promotion",
    "Consultation Campaign": "Consultation",
    "Financing Campaign": "Financing",
    "Educational Campaign": "Education",
    "Wellness Campaign": "Lifestyle Wellness",
}

PRODUCT_ALTERNATIVES = {
    "Master V9": ("Master V7", "Pause M10"),
    "Master V7": ("Master V9", "Master V6"),
    "Master V6": ("Master V7", "Master V5"),
    "Master V5": ("Master V6", "Master S4"),
    "Master S4": ("Master V5", "Pause M4"),
    "Pause M10": ("Master V9", "Master V7"),
    "Pause M6": ("Pause M4", "Pause M6s"),
    "Pause M6s": ("Pause M6", "Pause M4"),
    "Pause M4": ("Pause M6", "Master S4"),
}
