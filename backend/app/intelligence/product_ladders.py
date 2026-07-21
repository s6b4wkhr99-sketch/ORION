"""Explicit product recommendation order ladders for Ceragem + PRIZM segments.

Single source of truth for:
- Rule-065 primary product selection (1st rank = recommended_product)
- Mission Control / Market Intelligence segment hover product lists

Conflict rule: Pain High or Ceragem Pain-axis → Ceragem ladder wins over PRIZM.
Wellness-dominant profiles use the PRIZM ladder. Mixed / medium pain uses a joint ladder.
Nudges only move up/down within the active ladder — they never invent SKUs outside it.
"""

from __future__ import annotations

from app.intelligence.ceragem_rules import (
    compose_ceragem_segment,
    parse_ceragem_axis,
    parse_ceragem_tier,
    segment_axis_is_pain,
)
from app.intelligence.promotion_policy_constants import WELLNESS_V_WEIGHT

# A. Ceragem Segment → product order (1 → n)
CERAGEM_PRODUCT_LADDERS: dict[str, tuple[str, ...]] = {
    "High+ · Wellness": ("Master V9", "Master V7", "Pause M10", "Master V6"),
    "High+ · Pain Index": ("Master V7", "Master V6", "Master V5", "Master S4"),
    "Mid-High+ · Wellness": ("Master V7", "Pause M10", "Master V6", "Pause M6"),
    "Mid-High+ · Pain Index": ("Master V6", "Master V5", "Pause M6", "Master S4"),
    "Mid+ · Wellness": ("Pause M6s", "Pause M6", "Pause M4", "Pause M10"),
    "Mid+ · Pain Index": ("Master V6", "Master V5", "Master S4", "Pause M4"),
    "Mid-Low+ · Wellness": ("Pause M6s", "Pause M6", "Pause M4", "Master S4"),
    "Mid-Low+ · Pain Index": ("Master V5", "Master V6", "Master S4", "Pause M4"),
    "Low+ · Wellness": ("Master S4", "Pause M6s", "Pause M4", "Pause M10"),
    "Low+ · Pain Index": ("Master S4", "Master V5", "Pause M4", "Master V6"),
}

# B. PRIZM → product order (1 → n)
PRIZM_PRODUCT_LADDERS: dict[str, tuple[str, ...]] = {
    "Established Elite": ("Master V9", "Pause M10", "Master V7", "Pause M6"),
    "Suburban Sophisticates": ("Master V9", "Master V7", "Pause M10", "Master V6"),
    "Booming with Confidence": ("Master V7", "Master V6", "Pause M10", "Pause M6"),
    "Kids and Cul-de-Sacs": ("Pause M6s", "Pause M6", "Pause M4", "Master S4"),
    "Wellness Seekers": ("Master V7", "Pause M6s", "Pause M6", "Master V6"),
    "Aging in Place": ("Pause M6s", "Pause M4", "Master S4", "Master V5"),
    "Caregiving Households": ("Master S4", "Pause M6s", "Pause M4", "Master V5"),
    "Simple Life": ("Master S4", "Pause M6s", "Pause M4", "Master V5"),
    "Unknown": ("Pause M4", "Pause M6s", "Master S4", "Pause M6"),
}

_VALUE_PRIZM = frozenset({"Simple Life", "Caregiving Households", "Unknown"})
_FAMILY_VALUE_PRIZM = frozenset(
    {"Simple Life", "Caregiving Households", "Unknown", "Kids and Cul-de-Sacs", "Aging in Place"},
)
_DEFAULT_CERAGEM_KEY = "Mid-Low+ · Wellness"

# Value-tier standards for lower-income ZIPs (baseline before promo expansion).
STANDARD_VALUE_M_SKU = "Pause M4"  # M-series entry — core massage function at lowest M price
STANDARD_VALUE_S_SKU = "Master S4"  # V-line value entry (Pause S4 deprecated)

_FLAGSHIP_V_SKU = "Master V9"
_PREMIUM_M_SKU = "Pause M10"
_PREMIUM_V6_SKU = "Master V6"
_V_LINE_SKUS = frozenset({"Master V9", "Master V7", "Master V6", "Master V5", "Master S4"})
_M_LINE_SKUS = frozenset({"Pause M10", "Pause M6", "Pause M6s", "Pause M4"})

_PP_SCORE_FROM_CATEGORY = {"High": 72.0, "Medium": 52.0, "Low": 32.0}


def is_high_end_purchase_zip(
    *,
    premium_zip: bool,
    zip_income_tier: str,
    purchase_power_category: str,
) -> bool:
    """ZIPs that can realistically support Master V9 / Pause M10 flagship pricing."""
    if premium_zip:
        return True
    if zip_income_tier == "High" and purchase_power_category == "High":
        return True
    return False


def is_affluent_purchase_zip(
    *,
    premium_zip: bool,
    zip_income_tier: str,
    purchase_power_category: str,
) -> bool:
    """Mid-high V-line SKUs (V6/V7) — broader than flagship but not value ZIPs."""
    if is_high_end_purchase_zip(
        premium_zip=premium_zip,
        zip_income_tier=zip_income_tier,
        purchase_power_category=purchase_power_category,
    ):
        return True
    if zip_income_tier == "High" and purchase_power_category in {"High", "Medium"}:
        return True
    if zip_income_tier == "Mid" and purchase_power_category == "High":
        return True
    return False


def is_m10_eligible_zip(
    *,
    premium_zip: bool,
    zip_income_tier: str,
    purchase_power_category: str,
) -> bool:
    """Pause M10 — nationwide when High PP + High/Mid income, or flagship high-end ZIP."""
    if is_high_end_purchase_zip(
        premium_zip=premium_zip,
        zip_income_tier=zip_income_tier,
        purchase_power_category=purchase_power_category,
    ):
        return True
    return purchase_power_category == "High" and zip_income_tier in {"High", "Mid"}


def _purchase_power_score(
    purchase_power_category: str,
    zip_income_tier: str,
) -> float:
    score = _PP_SCORE_FROM_CATEGORY.get(purchase_power_category, 50.0)
    if zip_income_tier == "Lower":
        score -= 8.0
    elif zip_income_tier == "High":
        score += 8.0
    return score


def is_post_promo_v_accessible(
    product: str,
    *,
    purchase_power_category: str,
    zip_income_tier: str,
) -> bool:
    """Standing V5/V6 promo makes post-promo price reachable beyond affluent-only geo."""
    from app.commercial.promotion_policy import is_promotion_active
    from app.intelligence.promo_price_response import is_post_promo_accessible

    if product not in {"Master V5", "Master V6", "Master V7"}:
        return False
    promo_active = is_promotion_active(product) or (
        product == "Master V7" and is_promotion_active("Master V6")
    )
    if not promo_active:
        return False

    resolved = "Master V6" if product == "Master V7" else product
    return is_post_promo_accessible(
        resolved,
        purchase_power_category=purchase_power_category,
        zip_income_tier=zip_income_tier,
    )


def merge_joint_ladder(ceragem: list[str], prizm: list[str]) -> list[str]:
    """Interleave V-line (pain/Ceragem) and M-line (wellness/PRIZM) rungs for mixed profiles."""
    v_items = [sku for sku in ceragem if sku in _V_LINE_SKUS]
    m_items = [sku for sku in prizm if sku in _M_LINE_SKUS]
    for sku in ceragem:
        if sku in _M_LINE_SKUS and sku not in m_items:
            m_items.append(sku)
    for sku in prizm:
        if sku in _V_LINE_SKUS and sku not in v_items:
            v_items.append(sku)

    merged: list[str] = []
    vi = mi = 0
    while vi < len(v_items) or mi < len(m_items):
        if vi < len(v_items):
            merged.append(v_items[vi])
            vi += 1
        if mi < len(m_items):
            merged.append(m_items[mi])
            mi += 1

    seen: set[str] = set()
    result: list[str] = []
    for sku in merged:
        if sku in seen:
            continue
        seen.add(sku)
        result.append(sku)
    return result


def _step_down_ladder(picked: str, ladder: list[str]) -> str:
    try:
        idx = ladder.index(picked)
    except ValueError:
        return picked
    return ladder[min(idx + 1, len(ladder) - 1)]


def cap_flagship_v9_to_premium_zip(
    picked: str,
    ladder: list[str],
    *,
    premium_zip: bool,
    zip_income_tier: str,
    purchase_power_category: str,
) -> str:
    """Keep Master V9 on premium ZIP or High income + High PP only."""
    if picked != _FLAGSHIP_V_SKU:
        return picked
    if is_high_end_purchase_zip(
        premium_zip=premium_zip,
        zip_income_tier=zip_income_tier,
        purchase_power_category=purchase_power_category,
    ):
        return picked
    try:
        idx = ladder.index(_FLAGSHIP_V_SKU)
    except ValueError:
        return picked
    return ladder[min(idx + 1, len(ladder) - 1)]


def cap_premium_skus_to_geo(
    picked: str,
    ladder: list[str],
    *,
    premium_zip: bool,
    zip_income_tier: str,
    purchase_power_category: str,
    customer_state: str | None = None,
    pain_index_category: str = "Low",
    ceragem_segment: str | None = None,
) -> str:
    """Keep flagship / premium SKUs on ZIPs with real purchase power (promo-aware for V6/V7)."""
    if picked == _FLAGSHIP_V_SKU:
        return cap_flagship_v9_to_premium_zip(
            picked,
            ladder,
            premium_zip=premium_zip,
            zip_income_tier=zip_income_tier,
            purchase_power_category=purchase_power_category,
        )

    high_end = is_high_end_purchase_zip(
        premium_zip=premium_zip,
        zip_income_tier=zip_income_tier,
        purchase_power_category=purchase_power_category,
    )
    affluent = is_affluent_purchase_zip(
        premium_zip=premium_zip,
        zip_income_tier=zip_income_tier,
        purchase_power_category=purchase_power_category,
    )

    if picked == _PREMIUM_M_SKU:
        return picked if is_m10_eligible_zip(
            premium_zip=premium_zip,
            zip_income_tier=zip_income_tier,
            purchase_power_category=purchase_power_category,
        ) else _step_down_ladder(picked, ladder)

    if picked in {_PREMIUM_V6_SKU, "Master V7"}:
        if affluent:
            return picked
        if is_post_promo_v_accessible(
            picked,
            purchase_power_category=purchase_power_category,
            zip_income_tier=zip_income_tier,
        ):
            return picked
        return _step_down_ladder(picked, ladder)

    if picked == "Master V5" and (
        segment_axis_is_pain(ceragem_segment) or pain_index_category in {"High", "Medium"}
    ):
        if affluent or is_post_promo_v_accessible(
            "Master V5",
            purchase_power_category=purchase_power_category,
            zip_income_tier=zip_income_tier,
        ):
            return picked

    return picked


def is_lower_income_context(
    *,
    zip_income_tier: str,
    purchase_power_category: str,
    premium_zip: bool = False,
) -> bool:
    if premium_zip:
        return False
    if zip_income_tier == "Lower":
        return True
    if purchase_power_category == "Low" and zip_income_tier != "High":
        return True
    return False


def apply_standard_value_pick(
    picked: str,
    *,
    ladder: list[str],
    prizm_segment: str | None,
    purchase_power_category: str,
    lifestyle_category: str,
    zip_income_tier: str,
    pain_index_category: str,
    ceragem_segment: str | None,
    premium_zip: bool = False,
) -> str:
    """Anchor lower-income ZIP picks to Pause M4 / Pause S4 before promo expansion."""
    from app.commercial.promotion_policy import is_promotion_active

    if not is_lower_income_context(
        zip_income_tier=zip_income_tier,
        purchase_power_category=purchase_power_category,
        premium_zip=premium_zip,
    ):
        return picked

    pain_axis = segment_axis_is_pain(ceragem_segment) or pain_index_category in {"High", "Medium"}

    # Promo-active V-line: keep FDA standing promos on pain ZIPs nationwide.
    if pain_axis and is_promotion_active("Master V6") and picked in {"Master V6", "Master V7"}:
        if is_post_promo_v_accessible(
            picked if picked != "Master V7" else "Master V6",
            purchase_power_category=purchase_power_category,
            zip_income_tier=zip_income_tier,
        ):
            return picked
    if pain_axis and is_promotion_active("Master V5") and picked in {"Master V5", "Master V6"}:
        if is_post_promo_v_accessible(
            "Master V5",
            purchase_power_category=purchase_power_category,
            zip_income_tier=zip_income_tier,
        ):
            return picked

    if picked in {"Master V9", "Master V7", "Pause M10", "Master V6"}:
        lowest_m = next(
            (sku for sku in (STANDARD_VALUE_M_SKU, "Pause M6", "Pause M6s", "Pause M10") if sku in ladder),
            None,
        )
        if lowest_m:
            return lowest_m
        if STANDARD_VALUE_S_SKU in ladder:
            return STANDARD_VALUE_S_SKU
        return picked

    prizm_key = normalize_prizm_key(prizm_segment)

    if pain_axis:
        if lifestyle_category == "Low" and STANDARD_VALUE_M_SKU in ladder:
            return STANDARD_VALUE_M_SKU
        if STANDARD_VALUE_S_SKU in ladder and picked in {
            STANDARD_VALUE_S_SKU,
            STANDARD_VALUE_M_SKU,
            "Master V5",
            "Master V6",
            "Master S4",
        }:
            if is_promotion_active(STANDARD_VALUE_S_SKU):
                return STANDARD_VALUE_S_SKU
            return STANDARD_VALUE_M_SKU if STANDARD_VALUE_M_SKU in ladder else picked
        return picked

    if prizm_key in _FAMILY_VALUE_PRIZM and STANDARD_VALUE_S_SKU in ladder:
        if lifestyle_category == "Low" or zip_income_tier == "Lower":
            if is_promotion_active(STANDARD_VALUE_S_SKU):
                return STANDARD_VALUE_S_SKU
            return STANDARD_VALUE_M_SKU if STANDARD_VALUE_M_SKU in ladder else picked

    if STANDARD_VALUE_M_SKU in ladder and picked in {
        "Pause M6",
        "Pause M6s",
        STANDARD_VALUE_M_SKU,
        STANDARD_VALUE_S_SKU,
    }:
        if picked in {STANDARD_VALUE_M_SKU, STANDARD_VALUE_S_SKU}:
            return picked
        return STANDARD_VALUE_M_SKU

    return picked


def ceragem_ladder_key(segment: str | None) -> str:
    return compose_ceragem_segment(parse_ceragem_tier(segment), parse_ceragem_axis(segment))


def ladder_for_ceragem(segment: str | None) -> list[str]:
    key = ceragem_ladder_key(segment)
    return list(CERAGEM_PRODUCT_LADDERS.get(key, CERAGEM_PRODUCT_LADDERS[_DEFAULT_CERAGEM_KEY]))


def normalize_prizm_key(prizm: str | None) -> str:
    key = (prizm or "Unknown").strip()
    if key in {"Unclassified", ""}:
        return "Unknown"
    return key if key in PRIZM_PRODUCT_LADDERS else "Unknown"


def ladder_for_prizm(prizm: str | None) -> list[str]:
    return list(PRIZM_PRODUCT_LADDERS[normalize_prizm_key(prizm)])


def resolve_active_ladder(
    *,
    ceragem_segment: str | None,
    prizm_segment: str | None,
    pain_index_category: str,
    premium_zip: bool = False,
) -> tuple[list[str], str]:
    """Return (ladder, source) with source in {'ceragem', 'prizm', 'joint'}."""
    ceragem = ladder_for_ceragem(ceragem_segment)
    prizm_key = normalize_prizm_key(prizm_segment)
    prizm = ladder_for_prizm(prizm_key)

    pain_dominant = pain_index_category == "High" or segment_axis_is_pain(ceragem_segment)
    wellness_dominant = pain_index_category == "Low" and not segment_axis_is_pain(ceragem_segment)

    if pain_dominant:
        return ceragem, "ceragem"
    if wellness_dominant:
        if premium_zip and prizm_key != "Established Elite":
            return ladder_for_prizm("Established Elite"), "prizm"
        return prizm, "prizm"
    return merge_joint_ladder(ceragem, prizm), "joint"


def _ladder_index(
    ladder: list[str],
    *,
    source: str,
    prizm_segment: str | None,
    purchase_power_category: str,
    lifestyle_category: str,
    zip_income_tier: str,
) -> int:
    prizm_key = normalize_prizm_key(prizm_segment)
    idx = 0

    if source == "prizm" and prizm_key in _VALUE_PRIZM:
        if lifestyle_category == "High" and purchase_power_category in {"High", "Medium"}:
            idx = 1
        elif lifestyle_category == "Medium" and (
            purchase_power_category == "Medium" or prizm_key == "Caregiving Households"
        ):
            idx = 1
        else:
            idx = 0
    else:
        if purchase_power_category == "Low":
            idx += 1
        if lifestyle_category == "Low":
            idx += 1
        elif lifestyle_category == "High" and purchase_power_category in {"High", "Medium"}:
            idx = max(0, idx - 1)
        if zip_income_tier == "Lower":
            idx += 1
        elif zip_income_tier == "High" and purchase_power_category in {"High", "Medium"}:
            idx = max(0, idx - 1)

    # Wellness high-PP profiles — slight V-line weighting within ladder
    if (
        WELLNESS_V_WEIGHT > 0
        and source in {"prizm", "joint"}
        and purchase_power_category in {"High", "Medium"}
        and lifestyle_category in {"High", "Medium"}
    ):
        v_idx = next((i for i, sku in enumerate(ladder) if sku in _V_LINE_SKUS), None)
        if v_idx is not None and v_idx < idx:
            idx = max(v_idx, idx - 1)

    return min(max(idx, 0), len(ladder) - 1)


def _pick_from_ladder_core(
    ladder: list[str],
    *,
    source: str,
    prizm_segment: str | None,
    purchase_power_category: str,
    lifestyle_category: str,
    zip_income_tier: str,
    customer_state: str | None,
    pain_index_category: str,
    ceragem_segment: str | None,
    premium_zip: bool,
) -> str:
    if not ladder:
        return "Master S4"

    idx = _ladder_index(
        ladder,
        source=source,
        prizm_segment=prizm_segment,
        purchase_power_category=purchase_power_category,
        lifestyle_category=lifestyle_category,
        zip_income_tier=zip_income_tier,
    )
    picked = ladder[idx]
    picked = apply_standard_value_pick(
        picked,
        ladder=ladder,
        prizm_segment=prizm_segment,
        purchase_power_category=purchase_power_category,
        lifestyle_category=lifestyle_category,
        zip_income_tier=zip_income_tier,
        pain_index_category=pain_index_category,
        ceragem_segment=ceragem_segment,
        premium_zip=premium_zip,
    )
    return cap_premium_skus_to_geo(
        picked,
        ladder,
        premium_zip=premium_zip,
        zip_income_tier=zip_income_tier,
        purchase_power_category=purchase_power_category,
        customer_state=customer_state,
        pain_index_category=pain_index_category,
        ceragem_segment=ceragem_segment,
    )


def pick_primary_from_ladder(
    ladder: list[str],
    *,
    source: str,
    prizm_segment: str | None,
    purchase_power_category: str,
    lifestyle_category: str,
    zip_income_tier: str,
    customer_state: str | None = None,
    pain_index_category: str = "Low",
    ceragem_segment: str | None = None,
    premium_zip: bool = False,
) -> str:
    """Select the 1st recommended SKU; joint fallback when primary axis yields thin modus."""
    picked = _pick_from_ladder_core(
        ladder,
        source=source,
        prizm_segment=prizm_segment,
        purchase_power_category=purchase_power_category,
        lifestyle_category=lifestyle_category,
        zip_income_tier=zip_income_tier,
        customer_state=customer_state,
        pain_index_category=pain_index_category,
        ceragem_segment=ceragem_segment,
        premium_zip=premium_zip,
    )

    pain_axis = segment_axis_is_pain(ceragem_segment) or pain_index_category in {"High", "Medium"}
    wellness_axis = not segment_axis_is_pain(ceragem_segment) and pain_index_category == "Low"

    if pain_axis and picked not in _V_LINE_SKUS:
        ceragem_ladder = ladder_for_ceragem(ceragem_segment)
        alt = _pick_from_ladder_core(
            ceragem_ladder,
            source="ceragem",
            prizm_segment=prizm_segment,
            purchase_power_category=purchase_power_category,
            lifestyle_category=lifestyle_category,
            zip_income_tier=zip_income_tier,
            customer_state=customer_state,
            pain_index_category=pain_index_category,
            ceragem_segment=ceragem_segment,
            premium_zip=premium_zip,
        )
        if alt in _V_LINE_SKUS:
            return alt

    if wellness_axis and picked not in _M_LINE_SKUS:
        prizm_ladder = ladder_for_prizm(prizm_segment)
        alt = _pick_from_ladder_core(
            prizm_ladder,
            source="prizm",
            prizm_segment=prizm_segment,
            purchase_power_category=purchase_power_category,
            lifestyle_category=lifestyle_category,
            zip_income_tier=zip_income_tier,
            customer_state=customer_state,
            pain_index_category=pain_index_category,
            ceragem_segment=ceragem_segment,
            premium_zip=premium_zip,
        )
        if alt in _M_LINE_SKUS:
            return alt

    return picked


def merge_ladder_with_observed(
    ladder: list[str],
    top_recommended: list[str] | None,
    *,
    limit: int = 6,
) -> list[str]:
    """Dashboard hover order: ladder first, then observed recommendation counts."""
    result: list[str] = []
    seen: set[str] = set()
    for product in list(ladder) + list(top_recommended or []):
        if not product or product in seen:
            continue
        seen.add(product)
        result.append(product)
        if len(result) >= limit:
            break
    return result
