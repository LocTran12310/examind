"""Business time zone (ui-standards A-04, one fixed zone).

Timestamps are stored as `timestamptz` and sent as ISO UTC (`…Z`); a *day* (filters, school years,
terms) is a calendar day in `settings.business_tz` (Asia/Ho_Chi_Minh), whatever the server's TZ.
"""
from datetime import UTC, date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from app.core.config import get_settings


@lru_cache
def business_tz() -> ZoneInfo:
    return ZoneInfo(get_settings().business_tz)


def business_today(now: datetime | None = None) -> date:
    return business_date(now or datetime.now(UTC))


def business_date(when: datetime | date) -> date:
    """The business calendar day of an instant (naive datetimes are taken as UTC)."""
    if not isinstance(when, datetime):
        return when
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return when.astimezone(business_tz()).date()


def day_start(d: date) -> datetime:
    """00:00 of the business day `d`, as a UTC instant."""
    return datetime.combine(d, time.min, tzinfo=business_tz()).astimezone(UTC)


def day_end_exclusive(d: date) -> datetime:
    """00:00 of the next business day, as a UTC instant (half-open upper bound)."""
    return day_start(d + timedelta(days=1))
