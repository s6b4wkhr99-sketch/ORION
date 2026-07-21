"""Ceragem Segment — purchase-power tier (baseline) + product-recommendation axis."""

from __future__ import annotations

from dataclasses import dataclass

from app.reference.registry import CERAGEM_SEGMENT_V04

CERAGEM_TIERS = ("High+", "Mid-High+", "Mid+", "Mid-Low+", "Low+")
SEGMENT_AXES = ("Wellness", "Pain Index")
CERAGEM_SEGMENT_SEPARATOR = " · "

CERAGEM_SEGMENTS = list(CERAGEM_SEGMENT_V04)

WELLNESS_PRIZM = {"Established Elite", "Suburban Sophisticates", "Wellness Seekers", "Booming with Confidence"}
PAIN_PRIZM = {"Aging in Place", "Caregiving Households", "Simple Life"}

_LEGACY_TIER_MAP = {
    "High": "High+",
    "Mid-High": "Mid-High+",
    "Mid": "Mid+",
    "Mid-Low": "Mid-Low+",
    "Low": "Low+",
}


def compose_ceragem_segment(tier: str, axis: str) -> str:
    """Baseline tier + recommendation axis (display / storage)."""
    return f"{tier}{CERAGEM_SEGMENT_SEPARATOR}{axis}"


def parse_ceragem_tier(segment: str | None) -> str:
    if not segment:
        return "Mid-Low+"
    text = segment.strip()
    if CERAGEM_SEGMENT_SEPARATOR in text:
        return text.split(CERAGEM_SEGMENT_SEPARATOR, 1)[0].strip()
    if " + " in text:
        legacy = text.split(" + ", 1)[0].strip()
        if legacy.endswith("+"):
            return legacy
        return _LEGACY_TIER_MAP.get(legacy, f"{legacy}+")
    if text.endswith("+"):
        return text
    return _LEGACY_TIER_MAP.get(text, text)


def parse_ceragem_axis(segment: str | None) -> str:
    if not segment:
        return "Wellness"
    text = segment.strip()
    if CERAGEM_SEGMENT_SEPARATOR in text:
        axis = text.split(CERAGEM_SEGMENT_SEPARATOR, 1)[1].strip()
        return axis if axis in SEGMENT_AXES else "Wellness"
    if " + " in text:
        axis = text.split(" + ", 1)[1].strip()
        return axis if axis in SEGMENT_AXES else "Wellness"
    return "Wellness"


def segment_axis_is_pain(segment: str | None) -> bool:
    return parse_ceragem_axis(segment) == "Pain Index"


def tier_rank(tier: str) -> int:
    order = {name: idx for idx, name in enumerate(CERAGEM_TIERS)}
    return order.get(parse_ceragem_tier(tier), 2)


def axis_rank(segment: str | None) -> int:
    """Pain Index before Wellness for legend / distribution ordering."""
    axis = parse_ceragem_axis(segment)
    if axis == "Pain Index":
        return 0
    if axis == "Wellness":
        return 1
    return 2


def ceragem_segment_sort_key(segment: str | None) -> tuple[int, int, str]:
    """Sort: tier (High+ → Low+), then axis (Pain Index → Wellness)."""
    text = (segment or "").strip()
    return (tier_rank(text), axis_rank(text), text)


def resolve_ceragem_tier(ctx) -> str:
    """
    Purchase-power baseline tier from final PP index + ZIP/geo signals.
    Runs after Purchase Power engine (Section 21 reorder).

    Bands align to PP clusters (0.25 / 0.55 / 0.75) with geographic affluence
    so Mid-High+ is populated between premium High+ and core Mid+.
    """
    zip_intel = ctx.zip_intelligence or {}
    pp_index = float(ctx.purchase_power_index or 0)
    pp_cat = (ctx.purchase_power_category or "").strip()
    if pp_cat not in {"High", "Medium", "Low"}:
        pp_cat = "High" if pp_index >= 0.75 else "Medium" if pp_index >= 0.55 else "Low"

    premium = bool(zip_intel.get("premium_zip_indicator"))
    zip_tier = str(zip_intel.get("income_tier") or "Unknown")
    zip_potential = float(zip_intel.get("purchase_potential_score") or 0)
    geo = float(zip_intel.get("geographic_purchasing_context") or 0)

    score = min(1.0, pp_index * 0.72 + zip_potential * 0.16 + geo * 0.12)
    if premium:
        score = min(1.0, score + 0.05)
    elif zip_tier == "High":
        score = min(1.0, score + 0.04)
    elif zip_tier == "Mid":
        score = min(1.0, score + 0.02)

    if premium or pp_index >= 0.75:
        return "High+"
    if pp_cat == "Medium" and (zip_tier in {"High", "Mid"} or geo >= 0.35 or score >= 0.50):
        return "Mid-High+"
    if pp_cat == "Medium" or score >= 0.38:
        return "Mid+"
    if score >= 0.26:
        return "Mid-Low+"
    return "Low+"


def resolve_segment_axis(ctx) -> str:
    """Pain vs Wellness — product recommendation factor, not purchase tier."""
    prizm = ctx.prizm_proxy_segment or "Unknown"
    pain = float(ctx.pain_index or 0)
    lifestyle = float(ctx.lifestyle_index or 0)

    if prizm in PAIN_PRIZM and pain >= 0.4:
        return "Pain Index"
    if prizm in WELLNESS_PRIZM and lifestyle >= 0.35 and pain < lifestyle:
        return "Wellness"
    if pain >= lifestyle + 0.06:
        return "Pain Index"
    return "Wellness"


@dataclass
class CeragemInputs:
    tier: str
    axis: str
    segment: str
    purchase_power_index: float
    pain_index: float
    lifestyle_index: float
    prizm_segment: str
    premium_zip_indicator: bool
    geographic_purchasing_context: float


def build_ceragem_inputs(ctx) -> CeragemInputs:
    tier = resolve_ceragem_tier(ctx)
    axis = resolve_segment_axis(ctx)
    zip_intel = ctx.zip_intelligence or {}
    return CeragemInputs(
        tier=tier,
        axis=axis,
        segment=compose_ceragem_segment(tier, axis),
        purchase_power_index=float(ctx.purchase_power_index or 0),
        pain_index=float(ctx.pain_index or 0),
        lifestyle_index=float(ctx.lifestyle_index or 0),
        prizm_segment=ctx.prizm_proxy_segment or "Unknown",
        premium_zip_indicator=bool(zip_intel.get("premium_zip_indicator")),
        geographic_purchasing_context=float(zip_intel.get("geographic_purchasing_context") or 0),
    )


def assign_ceragem_segment_from_context(ctx) -> str:
    """Primary assignment — tier from PP, axis from pain/lifestyle/PRIZM."""
    inputs = build_ceragem_inputs(ctx)
    return inputs.segment
