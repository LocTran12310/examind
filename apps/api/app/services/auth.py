"""Login, lockout, refresh-token rotation, logout, password change (ADR-02, ADR-05)."""
from dataclasses import dataclass
from datetime import timedelta
import re

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, validation
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    new_refresh_token,
    now,
    verify_password,
)
from app.models import Organization, RefreshToken, User

INVALID = AppError("invalid_credentials", "Sai tổ chức, tên đăng nhập hoặc mật khẩu", 401)
SUSPENDED = AppError("org_suspended", "Tổ chức đang bị khóa", 403)
ORG_CODE_RE = re.compile(r"^[a-z0-9-]{3,32}$")
MIN_PASSWORD = 8


@dataclass
class Session_:
    user: User
    access_token: str
    refresh_token: str
    org: Organization | None = None
    role: str = ""


def normalise_org_code(code: str) -> str:
    return (code or "").strip().lower()


def _issue(db: Session, user: User, org: Organization | None = None, role: str | None = None) -> Session_:
    """Tokens for the active org: the given one, else the last used, else home (ADR-03, A-07)."""
    from app.services.membership import active_org

    if org is None or role is None:
        org, role = active_org(db, user)
    s = get_settings()
    raw, digest = new_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=digest, expires_at=now() + timedelta(days=s.refresh_token_days)))
    access = create_access_token(user.id, org.id, org.code, role)
    return Session_(user=user, access_token=access, refresh_token=raw, org=org, role=role)


def switch_org(db: Session, user: User, org_id, raw_refresh: str | None) -> Session_:
    from app.services.membership import switch

    org, role = switch(db, user, org_id)
    logout(db, raw_refresh)  # rotate: the old refresh token must not reopen the previous org
    return _issue(db, user, org, role)


def login(db: Session, org_code: str, username: str, password: str) -> Session_:
    s = get_settings()
    org = db.scalar(select(Organization).where(Organization.code == normalise_org_code(org_code)))
    user = None
    if org is not None:
        user = db.scalar(
            select(User).where(User.organization_id == org.id, User.username == (username or "").strip())
        )
    if user is not None and user.locked_until and user.locked_until > now():
        minutes = max(1, int((user.locked_until - now()).total_seconds() // 60) + 1)
        raise AppError("locked", f"Tài khoản tạm khóa, thử lại sau {minutes} phút", 429)

    ok = verify_password(password or "", user.password_hash if user else None)
    if not ok or user is None or not user.is_active:
        if user is not None:
            _record_failure(db, user)
            db.commit()
        raise INVALID
    if not org.can_login:
        raise SUSPENDED

    user.failed_logins = 0
    user.first_failed_at = None
    user.locked_until = None
    user.last_login_at = now()
    return _issue(db, user)


def _record_failure(db: Session, user: User) -> None:
    s = get_settings()
    window = timedelta(minutes=s.login_lock_minutes)
    if user.first_failed_at is None or now() - user.first_failed_at > window:
        user.first_failed_at = now()
        user.failed_logins = 0
    user.failed_logins += 1
    if user.failed_logins >= s.login_max_failures:
        user.locked_until = now() + window


def refresh(db: Session, raw_token: str) -> Session_:
    unauth = AppError("unauthenticated", "Phiên đăng nhập đã hết hạn", 401)
    if not raw_token:
        raise unauth
    token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)))
    if token is None:
        raise unauth
    if token.revoked_at is not None:
        # A revoked token being replayed means it leaked: kill every session of that user.
        revoke_user_tokens(db, token.user_id)
        db.commit()
        raise unauth
    if token.expires_at <= now():
        raise unauth
    user = db.get(User, token.user_id)
    if user is None or not user.is_active or not user.organization.can_login:
        token.revoked_at = now()
        db.commit()
        raise unauth
    token.revoked_at = now()
    return _issue(db, user)


def logout(db: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == hash_token(raw_token), RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now())
    )


def revoke_user_tokens(db: Session, user_id) -> None:
    db.execute(
        update(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)).values(revoked_at=now())
    )


def revoke_org_tokens(db: Session, org_id) -> None:
    user_ids = select(User.id).where(User.organization_id == org_id)
    db.execute(
        update(RefreshToken).where(RefreshToken.user_id.in_(user_ids), RefreshToken.revoked_at.is_(None)).values(revoked_at=now())
    )


def validate_new_password(new_password: str) -> None:
    if len(new_password or "") < MIN_PASSWORD:
        raise validation(f"Mật khẩu tối thiểu {MIN_PASSWORD} ký tự", "new_password")


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password or "", user.password_hash):
        raise validation("Mật khẩu hiện tại không đúng", "current_password")
    validate_new_password(new_password)
    if current_password == new_password:
        raise validation("Mật khẩu mới phải khác mật khẩu cũ", "new_password")
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
