"""SKU migration rules — Ceragem segment × Pain × Lifestyle refinements (2026.07).

Pre-change baseline: Volume 19 v1.0 / rescore_premium_geo_v9_m10_v6_v1
Post-change: Volume 19 v1.1 + SKU_MIGRATION_RULE_VERSION
"""

from __future__ import annotations

from dataclasses import dataclass

from app.intelligence.ceragem_rules import segment_axis_is_pain, tier_rank

from app.intelligence.promotion_policy_constants import SKU_ALIAS_ENABLED, V_VALUE_ENTRY_SKU
from app.intelligence.v_m_anchor import migration_strength_applies

SKU_MIGRATION_RULE_VERSION = "2026.07-sku-migration-v2"
INTELLIGENCE_VERSION_PRE_MIGRATION = "Volume 19 v1.0"
INTELLIGENCE_VERSION_POST_MIGRATION = "Volume 19 v1.1"

LEGACY_V4_CODE = "Master V4"
V_ENTRY_SKU = V_VALUE_ENTRY_SKU

_INDEX_RANK = {"Low": 0, "Medium": 1, "High": 2}


def normalize_product_code(product: str | None) -> str:
    """Map legacy Master V4 / Pause S4 field values to Master S4."""
    code = (product or "").strip()
    if code == LEGACY_V4_CODE:
        return V_ENTRY_SKU
    if SKU_ALIAS_ENABLED and code == "Pause S4":
        return V_ENTRY_SKU
    return code


@dataclass(frozen=True)
class MigrationSegmentProfile:
    ceragem_tier_rank: int
    pain_axis: bool
    pain_index: str
    lifestyle: str
    purchase_power: str


def _profile(inputs) -> MigrationSegmentProfile:
    return MigrationSegmentProfile(
        ceragem_tier_rank=tier_rank(inputs.ceragem_segment),
        pain_axis=segment_axis_is_pain(inputs.ceragem_segment),
        pain_index=inputs.pain_index_category or "Low",
        lifestyle=inputs.lifestyle_category or "Low",
        purchase_power=inputs.purchase_power_category or "Low",
    )


def _pain_profile_for_v_entry(profile: MigrationSegmentProfile) -> bool:
    return profile.pain_axis or profile.pain_index in {"High", "Medium"}


def _v5_promo_accessible(inputs) -> bool:
    from app.commercial.promotion_policy import is_promotion_active
    from app.intelligence.product_ladders import is_post_promo_v_accessible

    if not is_promotion_active("Master V5"):
        return False
    return is_post_promo_v_accessible(
        "Master V5",
        purchase_power_category=inputs.purchase_power_category,
        zip_income_tier=inputs.zip_income_tier,
    )


def _v6_promo_accessible(inputs) -> bool:
    from app.commercial.promotion_policy import is_promotion_active
    from app.intelligence.product_ladders import is_post_promo_v_accessible

    if not is_promotion_active("Master V6"):
        return False
    return is_post_promo_v_accessible(
        "Master V6",
        purchase_power_category=inputs.purchase_power_category,
        zip_income_tier=inputs.zip_income_tier,
    )


def qualifies_m4_to_v5(profile: MigrationSegmentProfile, *, promo_ok: bool) -> bool:
    """Pause M4 → Master V5 when pain + promo price fit + mid/up tier or strong lifestyle."""
    if not promo_ok:
        return False
    if not _pain_profile_for_v_entry(profile):
        return False

    pain_r = _INDEX_RANK.get(profile.pain_index, 0)
    ls_r = _INDEX_RANK.get(profile.lifestyle, 0)
    pp_r = _INDEX_RANK.get(profile.purchase_power, 0)

    if profile.pain_index == "High" and profile.ceragem_tier_rank <= 2 and ls_r >= 1:
        return True
    if profile.pain_axis and profile.ceragem_tier_rank <= 1 and pp_r >= 1:
        return True
    if profile.pain_index == "Medium" and profile.lifestyle == "High" and pp_r >= 1:
        return True
    if profile.pain_axis and profile.ceragem_tier_rank <= 2 and pain_r >= 1 and pp_r >= 1:
        return True
    return False


def qualifies_v9_to_v7(profile: MigrationSegmentProfile) -> bool:
    """Master V9 → V7: high therapeutic need but relative step-down vs flagship."""
    if profile.ceragem_tier_rank > 2:
        return False
    if profile.pain_index == "Low" and not profile.pain_axis:
        return False

    pp_r = _INDEX_RANK.get(profile.purchase_power, 0)
    ls_r = _INDEX_RANK.get(profile.lifestyle, 0)
    pain_r = _INDEX_RANK.get(profile.pain_index, 0)

    if pp_r == 2 and ls_r >= 1 and pain_r >= 1:
        return True
    if pp_r == 1 and profile.lifestyle == "High" and profile.pain_index == "High":
        return True
    if profile.pain_axis and profile.ceragem_tier_rank <= 1 and pp_r >= 1:
        return True
    return False


def qualifies_m_mass_to_v7(profile: MigrationSegmentProfile) -> bool:
    """Pause M6s/M4 → Master V7 upsell."""
    if profile.ceragem_tier_rank > 2:
        return False
    if profile.pain_index != "High":
        return False
    if profile.purchase_power != "High":
        return False
    if profile.lifestyle not in {"High", "Medium"}:
        return False
    return profile.pain_axis or profile.pain_index == "High"


def qualifies_m_mass_to_v5(profile: MigrationSegmentProfile, *, promo_ok: bool) -> bool:
    """Pause M6s/M4 → Master V5 downsell/upsell (promo-aware)."""
    return qualifies_m4_to_v5(profile, promo_ok=promo_ok)


def qualifies_m_mass_to_s4(profile: MigrationSegmentProfile) -> bool:
    """Pause M6s/M4 → Master S4 when pain axis but value / lower lifestyle tier."""
    if not _pain_profile_for_v_entry(profile):
        return False
    if profile.ceragem_tier_rank >= 3:
        return True
    if profile.lifestyle == "Low":
        return True
    if profile.purchase_power == "Low" and profile.pain_index in {"Medium", "High"}:
        return True
    if profile.pain_axis and profile.lifestyle == "Medium" and profile.purchase_power == "Medium":
        return True
    return False


def qualifies_s4_to_v7(profile: MigrationSegmentProfile) -> bool:
    """Master S4 → Master V7 upsell."""
    return (
        profile.ceragem_tier_rank <= 1
        and profile.pain_index == "High"
        and profile.purchase_power == "High"
        and profile.lifestyle == "High"
        and profile.pain_axis
    )


def qualifies_s4_to_v6(profile: MigrationSegmentProfile, *, promo_ok: bool) -> bool:
    """Master S4 → Master V6 upsell (promo)."""
    if not promo_ok:
        return False
    if not profile.pain_axis and profile.pain_index not in {"High", "Medium"}:
        return False
    return profile.ceragem_tier_rank <= 2 and profile.pain_index in {"High", "Medium"}


def qualifies_s4_to_v5(profile: MigrationSegmentProfile, *, promo_ok: bool) -> bool:
    """Master S4 → Master V5 upsell."""
    if not promo_ok:
        return False
    if not profile.pain_axis and profile.pain_index not in {"High", "Medium"}:
        return False
    if profile.ceragem_tier_rank <= 2 and _INDEX_RANK.get(profile.purchase_power, 0) >= 1:
        return True
    if profile.pain_index == "High" and profile.lifestyle in {"Medium", "High"}:
        return True
    return False


def migrate_pause_m4(product: str, inputs, profile: MigrationSegmentProfile) -> str:
    """Rule 1: Pause M4 pain-path → Master S4; promo-fit subset → Master V5."""
    if product != "Pause M4":
        return product
    if not _pain_profile_for_v_entry(profile):
        return product
    promo_ok = _v5_promo_accessible(inputs)
    if qualifies_m4_to_v5(profile, promo_ok=promo_ok):
        return "Master V5"
    return V_ENTRY_SKU


def migrate_master_v9(product: str, inputs, profile: MigrationSegmentProfile) -> str:
    """Rule 2: Master V9 → Master V7 for near-premium therapeutic segment."""
    if product != "Master V9":
        return product
    if qualifies_v9_to_v7(profile):
        return "Master V7"
    return product


def migrate_m_mass(product: str, inputs, profile: MigrationSegmentProfile) -> str:
    """Rule 3: Pause M6s / Pause M4 → V7 upsell or V5 / Master S4 downsell."""
    if product not in {"Pause M6s", "Pause M4"}:
        return product
    if product == "Pause M4" and _pain_profile_for_v_entry(profile):
        return migrate_pause_m4(product, inputs, profile)

    promo_ok = _v5_promo_accessible(inputs)
    if qualifies_m_mass_to_v7(profile):
        return "Master V7"
    if qualifies_m_mass_to_v5(profile, promo_ok=promo_ok):
        return "Master V5"
    if qualifies_m_mass_to_s4(profile):
        return V_ENTRY_SKU
    return product


def migrate_master_s4(product: str, inputs, profile: MigrationSegmentProfile) -> str:
    """Rule 4: Master S4 → V7 / V6 / V5 upsell by relative V-line fit."""
    if product != V_ENTRY_SKU:
        return product

    v6_ok = _v6_promo_accessible(inputs)
    v5_ok = _v5_promo_accessible(inputs)

    if qualifies_s4_to_v7(profile):
        return "Master V7"
    if qualifies_s4_to_v6(profile, promo_ok=v6_ok):
        return "Master V6"
    if qualifies_s4_to_v5(profile, promo_ok=v5_ok):
        return "Master V5"
    return product


def apply_sku_migration(product: str, inputs) -> str:
    """Apply post-ladder SKU migration refinements (Rule-065 extension)."""
    product = normalize_product_code(product)
    profile = _profile(inputs)
    seed = getattr(inputs, "customer_id", None) or ""

    if not migration_strength_applies(seed):
        return normalize_product_code(product)

    product = migrate_master_v9(product, inputs, profile)
    product = migrate_m_mass(product, inputs, profile)
    product = migrate_master_s4(product, inputs, profile)

    return normalize_product_code(product)
