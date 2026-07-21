"""SFMC audience segment catalog — maps Segment ID/Code/Name to CIOS segmentation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SfmcAudienceSegment:
    segment_id: str
    segment_code: str
    segment_name: str
    cios_key: str
    cios_label: str
    channel_mix: str
    audience_tier: int
    campaign_priority: str
    campaign_types: tuple[str, ...]
    description: str

    @property
    def is_multi_channel(self) -> bool:
        return self.channel_mix == "multi_channel"


# Ceragem CIOS audience segmentation (SFMC export catalog).
SFMC_AUDIENCE_SEGMENTS: tuple[SfmcAudienceSegment, ...] = (
    SfmcAudienceSegment(
        segment_id="3596226",
        segment_code="SEG6AB685C7-1",
        segment_name="Email and Direct Mail - 1",
        cios_key="multi_channel_primary",
        cios_label="Multi-Channel Primary",
        channel_mix="multi_channel",
        audience_tier=1,
        campaign_priority="High",
        campaign_types=("Email", "Direct Mail"),
        description="Primary email + direct mail audience (tier 1).",
    ),
    SfmcAudienceSegment(
        segment_id="3596230",
        segment_code="SEG6AB685C7-2",
        segment_name="Email and Direct Mail - 2",
        cios_key="multi_channel_secondary",
        cios_label="Multi-Channel Secondary",
        channel_mix="multi_channel",
        audience_tier=2,
        campaign_priority="Medium",
        campaign_types=("Email", "Direct Mail"),
        description="Secondary email + direct mail audience (tier 2).",
    ),
    SfmcAudienceSegment(
        segment_id="3596231",
        segment_code="SEG6AB685C7-3",
        segment_name="Email and Direct Mail - 3",
        cios_key="multi_channel_tertiary",
        cios_label="Multi-Channel Tertiary",
        channel_mix="multi_channel",
        audience_tier=3,
        campaign_priority="Low",
        campaign_types=("Email", "Direct Mail"),
        description="Tertiary email + direct mail audience (tier 3).",
    ),
    SfmcAudienceSegment(
        segment_id="3596224",
        segment_code="SEG1-1",
        segment_name="Email Only - 1",
        cios_key="email_only_primary",
        cios_label="Email-Only Primary",
        channel_mix="email_only",
        audience_tier=1,
        campaign_priority="Medium",
        campaign_types=("Email",),
        description="Primary email-only audience (no direct mail).",
    ),
    SfmcAudienceSegment(
        segment_id="3596227",
        segment_code="SEG1-2",
        segment_name="Email Only - 2",
        cios_key="email_only_secondary",
        cios_label="Email-Only Secondary",
        channel_mix="email_only",
        audience_tier=2,
        campaign_priority="Low",
        campaign_types=("Email",),
        description="Secondary email-only audience (no direct mail).",
    ),
)

BY_SEGMENT_ID: dict[str, SfmcAudienceSegment] = {s.segment_id: s for s in SFMC_AUDIENCE_SEGMENTS}
BY_SEGMENT_CODE: dict[str, SfmcAudienceSegment] = {s.segment_code.upper(): s for s in SFMC_AUDIENCE_SEGMENTS}
BY_SEGMENT_NAME: dict[str, SfmcAudienceSegment] = {s.segment_name.casefold(): s for s in SFMC_AUDIENCE_SEGMENTS}
BY_CIOS_KEY: dict[str, SfmcAudienceSegment] = {s.cios_key: s for s in SFMC_AUDIENCE_SEGMENTS}


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def resolve_audience_segment(
    *,
    segment_id: str | None = None,
    segment_code: str | None = None,
    segment_name: str | None = None,
) -> SfmcAudienceSegment | None:
    """Resolve SFMC segment fields to the CIOS audience segmentation catalog."""
    sid = _clean(segment_id)
    if sid and sid in BY_SEGMENT_ID:
        return BY_SEGMENT_ID[sid]

    code = _clean(segment_code)
    if code:
        hit = BY_SEGMENT_CODE.get(code.upper())
        if hit:
            return hit

    name = _clean(segment_name)
    if name:
        hit = BY_SEGMENT_NAME.get(name.casefold())
        if hit:
            return hit

    return None


def audience_segment_payload(
    *,
    segment_id: str | None = None,
    segment_code: str | None = None,
    segment_name: str | None = None,
) -> dict[str, str | None]:
    """Normalize SFMC segment columns and attach resolved CIOS audience_segment key."""
    resolved = resolve_audience_segment(
        segment_id=segment_id,
        segment_code=segment_code,
        segment_name=segment_name,
    )
    if resolved:
        return {
            "sfmc_segment_id": resolved.segment_id,
            "sfmc_segment_code": resolved.segment_code,
            "sfmc_segment_name": resolved.segment_name,
            "audience_segment": resolved.cios_key,
        }

    return {
        "sfmc_segment_id": _clean(segment_id),
        "sfmc_segment_code": _clean(segment_code),
        "sfmc_segment_name": _clean(segment_name),
        "audience_segment": None,
    }
