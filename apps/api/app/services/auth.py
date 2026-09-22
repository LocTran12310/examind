"""Moved to app.modules.identity (architecture-refactor): thin wrappers over its handlers for the old layout and its tests.
Domain errors come back as the old AppError."""
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Organization, User
from app.modules.identity.application.commands.change_password import ChangePassword, ChangePasswordHandler
from app.modules.identity.application.commands.login import Login, LoginHandler
from app.modules.identity.application.commands.logout import Logout, LogoutHandler
from app.modules.identity.application.commands.refresh_session import RefreshSession, RefreshSessionHandler
from app.modules.identity.domain.services.accounts import check_new_password, normalise_org_code  # noqa: F401
from app.modules.identity.infrastructure.adapters.passwords import Argon2PasswordHasher
from app.modules.identity.infrastructure.adapters.tokens import TokenSecrets
from app.modules.identity.infrastructure.repositories import SqlOrganizationRepository, SqlRefreshTokenRepository, SqlUserRepository
from app.modules.identity.interface import deps
from app.shared.application.actor import Actor
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import DomainError
from app.shared.infrastructure.sql_unit_of_work import SqlUnitOfWork
from app.shared.interface.errors import status_of


@dataclass
class Session_:
    user: User
    access_token: str
    refresh_token: str
    org: Organization | None = None
    role: str = ""


class _NoThrottle:
    def hit(self, key: str) -> bool:
        return True


@contextmanager
def _app_errors():
    try:
        yield
    except DomainError as e:
        raise AppError(e.code, e.message, status_of(e), e.fields) from e


def _session(db: Session, run: Callable) -> Session_:
    with _app_errors():
        s = run()
    return Session_(user=db.get(User, s.me.id), access_token=s.access_token, refresh_token=s.refresh_token,
                    org=db.get(Organization, s.me.org.id), role=s.me.role)


def login(db: Session, org_code: str, username: str, password: str) -> Session_:
    handle = LoginHandler(SqlOrganizationRepository(db), SqlUserRepository(db), Argon2PasswordHasher(), deps._issuer(db), _NoThrottle(),
                          deps._policy(), SqlUnitOfWork(db))
    return _session(db, lambda: handle(Login(org_code, username, password)))


def refresh(db: Session, raw_token: str) -> Session_:
    handle = RefreshSessionHandler(SqlRefreshTokenRepository(db), SqlUserRepository(db), SqlOrganizationRepository(db), TokenSecrets(),
                                   deps._issuer(db), SqlUnitOfWork(db))
    return _session(db, lambda: handle(RefreshSession(raw_token)))


def logout(db: Session, raw_token: str | None) -> None:
    LogoutHandler(deps._issuer(db), SqlUnitOfWork(db))(Logout(raw_token))


def revoke_user_tokens(db: Session, user_id) -> None:
    SqlRefreshTokenRepository(db).revoke_user(user_id, utcnow())


def revoke_org_tokens(db: Session, org_id) -> None:
    SqlRefreshTokenRepository(db).revoke_org(org_id, utcnow())


def validate_new_password(new_password: str) -> None:
    with _app_errors():
        check_new_password(new_password)


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    actor = Actor(user_id=user.id, org_id=user.organization_id, role=user.role, is_super=user.is_super)
    with _app_errors():
        ChangePasswordHandler(SqlUserRepository(db), Argon2PasswordHasher(), SqlUnitOfWork(db))(actor, ChangePassword(current_password, new_password))
