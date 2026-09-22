"""Request-scoped dependencies of the old layout: the authenticated user, role gates and the tenant scope (ADR-03).
Authentication moved to app.modules.identity (architecture-refactor); these wrap it for the routers not moved yet."""
from collections.abc import Callable
from dataclasses import dataclass
import uuid

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import forbidden
from app.models import User
from app.modules.identity.interface.deps import (  # noqa: F401  (re-exported)
    ACCESS_COOKIE, PASSWORD_CHANGE_ALLOWED, REFRESH_COOKIE, actor_from_request, check_password_gate, principal,
)


def _principal(request: Request, db: Session) -> tuple[User, uuid.UUID, str]:
    """(user, active org, role there) — re-checked on every request (ADR-03)."""
    p = principal(request, db)
    return p.user, p.org_id, p.role


def current_user_any(request: Request, db: Session = Depends(get_db)) -> User:
    """Authenticated, even if a password change is pending."""
    return _principal(request, db)[0]


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    p = principal(request, db)
    check_password_gate(request, p)
    return p.user


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


def staff_scope(scope: OrgScope = Depends(org_scope)) -> OrgScope:
    if scope.role not in STAFF:
        raise forbidden()
    return scope
