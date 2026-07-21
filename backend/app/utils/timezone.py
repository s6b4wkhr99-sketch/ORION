"""Application timezone helpers — Eastern Time (America/New_York, EST/EDT)."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.config import settings

DEFAULT_APP_TIMEZONE = "America/New_York"


def app_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(settings.app_timezone or DEFAULT_APP_TIMEZONE)
    except Exception:
        return ZoneInfo(DEFAULT_APP_TIMEZONE)


def app_timezone_label() -> str:
    tz = settings.app_timezone or DEFAULT_APP_TIMEZONE
    return "Eastern Time (EST/EDT)" if tz == DEFAULT_APP_TIMEZONE else tz


def now_app() -> datetime:
    """Current time in the configured application timezone."""
    return datetime.now(app_timezone())


def now_app_iso() -> str:
    return now_app().isoformat()


def to_app_tz(dt: datetime | None) -> datetime | None:
    """Convert a stored timestamp (naive UTC or aware) to app local time."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(app_timezone())


def format_app_datetime(dt: datetime | None, fmt: str = "%b %d, %I:%M %p %Z") -> str:
    local = to_app_tz(dt)
    return local.strftime(fmt) if local else ""


def format_app_date(dt: datetime | None, fmt: str = "%b %d") -> str:
    local = to_app_tz(dt)
    return local.strftime(fmt) if local else ""


def iso_app(dt: datetime | None) -> str | None:
    local = to_app_tz(dt)
    return local.isoformat() if local else None
