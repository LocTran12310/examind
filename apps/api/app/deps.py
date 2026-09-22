"""Request-scoped dependencies: the authenticated user, role gates and the tenant scope (ADR-03)."""
from collections.abc import Callable
from dataclasses import dataclass
import uuid

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError, forbidden
from app.core.security import decode_access_token
from app.models import User

ACCESS_COOKIE = "ex_access"
REFRESH_COOKIE = "ex_refresh"
UNAUTH = AppError("unauthenticated", "Bạn cần đăng nhập", 401)
# Routes a user with a temporary password may still use.
PASSWORD_CHANGE_ALLOWED = {"/api/auth/me", "/api/auth/change-password", "/api/auth/logout", "/api/auth/refresh"}


def _principal(request: Request, db: Session) -> tuple[User, uuid.UUID, str]:
    """(user, active org, role there) — re-checked on every request (ADR-03)."""
    cached = getattr(request.state, "principal", None)
    if cached is not None:
        return cached
    from app.models import Organization
    from app.services.membership import role_in

    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        header = request.headers.get("authorization", "")
        token = header[7:] if header.lower().startswith("bearer ") else None
    claims = decode_access_token(token) if token else None
    if not claims:
        raise UNAUTH
    user = db.get(User, uuid.UUID(claims["sub"]))
    if user is None or not user.is_active or not user.organization.can_login:
        raise UNAUTH
    org_id = uuid.UUID(claims.get("org_id") or str(user.organization_id))
    org = db.get(Organization, org_id)
    role = role_in(db, user, org_id) if org is not None and org.can_login else None
    if role is None:
        raise UNAUTH  # membership removed/disabled or org suspended: the client refreshes into an allowed org
    request.state.principal = (user, org_id, role)
    return request.state.principal


def current_user_any(request: Request, db: Session = Depends(get_db)) -> User:
    """Authenticated, even if a password change is pending."""
    return _principal(request, db)[0]


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = _principal(request, db)[0]
    if user.must_change_password and request.url.path not in PASSWORD_CHANGE_ALLOWED:
        raise AppError("password_change_required", "Bạn cần đổi mật khẩu trước khi tiếp tục", 403)
    return user


def require_role(*roles: str) -> Callable[..., User]:
    """Gate on the account's global role (super_admin lives in the system org whatever org is open)."""
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise forbidden()
        return user

    return dep


@dataclass(frozen=True)
class OrgScope:
    org_id: uuid.UUID
    user: User
    role: str
    is_super: bool = False


def org_scope(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)) -> OrgScope:
    _, org_id, role = _principal(request, db)
    return OrgScope(org_id=org_id, user=user, role=role, is_super=user.role == "super_admin")


STAFF = ("org_admin", "teacher")
