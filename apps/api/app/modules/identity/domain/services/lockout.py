"""Login lockout (ADR-05): too many failures inside the window lock the account for the window."""
from datetime import datetime, timedelta

from app.modules.identity.domain.entities import User


def locked_minutes(user: User, now: datetime) -> int | None:
    """Minutes left on a lock (at least 1), or None when the account is not locked."""
    if user.locked_until and user.locked_until > now:
        return max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
    return None


def record_failure(user: User, now: datetime, window: timedelta, max_failures: int) -> None:
    if user.first_failed_at is None or now - user.first_failed_at > window:
        user.first_failed_at = now
        user.failed_logins = 0
    user.failed_logins += 1
    if user.failed_logins >= max_failures:
        user.locked_until = now + window


def record_success(user: User, now: datetime) -> None:
    user.failed_logins = 0
    user.first_failed_at = None
    user.locked_until = None
    user.last_login_at = now
