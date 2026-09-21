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


def _user_from_request(request: Request, db: Session) -> User:
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
    return user


def current_user_any(request: Request, db: Session = Depends(get_db)) -> User:
    """Authenticated, even if a password change is pending."""
    return _user_from_request(request, db)


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = _user_from_request(request, db)
    if user.must_change_password and request.url.path not in PASSWORD_CHANGE_ALLOWED:
        raise AppError("password_change_required", "Bạn cần đổi mật khẩu trước khi tiếp tục", 403)
    return user


def require_role(*roles: str) -> Callable[..., User]:
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise forbidden()
        return user

    return dep


@dataclass(frozen=True)
class OrgScope:
    org_id: uuid.UUID
    user: User

    @property
    def role(self) -> str:
        return self.user.role


def org_scope(user: User = Depends(current_user)) -> OrgScope:
    return OrgScope(org_id=user.organization_id, user=user)


STAFF = ("org_admin", "teacher")
