"""Builds the identity handlers for a request and resolves who is calling (the Actor every module asks for)."""
from collections.abc import Callable
import uuid

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.modules.identity.application.api import IdentityApi
from app.modules.identity.application.commands.add_membership import AddMembershipHandler
from app.modules.identity.application.commands.change_org_status import ChangeOrgStatusHandler
from app.modules.identity.application.commands.change_password import ChangePasswordHandler
from app.modules.identity.application.commands.create_org import CreateOrgHandler
from app.modules.identity.application.commands.create_user import CreateUserHandler
from app.modules.identity.application.commands.delete_org import DeleteOrgHandler
from app.modules.identity.application.commands.import_users import CommitImportHandler, PreviewImportHandler
from app.modules.identity.application.commands.link_account import LinkAccountHandler
from app.modules.identity.application.commands.login import LoginHandler
from app.modules.identity.application.commands.logout import LogoutHandler
from app.modules.identity.application.commands.refresh_session import RefreshSessionHandler
from app.modules.identity.application.commands.remove_membership import RemoveMembershipHandler
from app.modules.identity.application.commands.reset_password import ResetPasswordHandler
from app.modules.identity.application.commands.switch_org import SwitchOrgHandler
from app.modules.identity.application.commands.unlink_account import UnlinkAccountHandler
from app.modules.identity.application.commands.update_membership import UpdateMembershipHandler
from app.modules.identity.application.commands.update_org import UpdateOrgHandler
from app.modules.identity.application.commands.update_user import UpdateUserHandler
from app.modules.identity.application.common import SessionIssuer
from app.modules.identity.application.dto import Principal
from app.modules.identity.application.ports import AuthPolicy, ClassDirectory, OrgSeeder
from app.modules.identity.application.queries.get_me import GetMeHandler
from app.modules.identity.application.queries.get_org import GetOrgHandler
from app.modules.identity.application.queries.get_user import GetUserHandler
from app.modules.identity.application.queries.my_orgs import MyOrgsHandler
from app.modules.identity.application.queries.resolve_principal import ResolvePrincipal, ResolvePrincipalHandler
from app.modules.identity.application.queries.search_accounts import SearchAccountsHandler
from app.modules.identity.application.queries.search_memberships import SearchOrgMembersHandler, SearchUserMembershipsHandler
from app.modules.identity.application.queries.search_orgs import SearchOrgsHandler
from app.modules.identity.application.queries.search_users import SearchUsersHandler
from app.modules.identity.domain import errors
from app.modules.identity.infrastructure.adapters.passwords import Argon2PasswordHasher
from app.modules.identity.infrastructure.adapters.rate_limit import SlidingWindow
from app.modules.identity.infrastructure.adapters.spreadsheets import FileSpreadsheetReader
from app.modules.identity.infrastructure.adapters.tokens import JwtAccessTokens, TokenSecrets
from app.modules.identity.infrastructure.read_models import SqlAccountReader, SqlMembershipReader, SqlOrgReader, SqlUserReader
from app.modules.identity.infrastructure.repositories import (
    SqlMembershipRepository,
    SqlOrganizationRepository,
    SqlRefreshTokenRepository,
    SqlUserRepository,
)
from app.shared.application.actor import Actor
from app.shared.domain.errors import Forbidden, Unauthenticated
from app.shared.infrastructure.config import get_settings
from app.shared.infrastructure.db import get_db
from app.shared.infrastructure.sql_audit import SqlAuditTrail
from app.shared.infrastructure.sql_unit_of_work import SqlUnitOfWork
from app.shared.interface.auth import current_actor

ACCESS_COOKIE = "ex_access"
REFRESH_COOKIE = "ex_refresh"
# Routes a user with a temporary password may still use.
PASSWORD_CHANGE_ALLOWED = {"/api/auth/me", "/api/auth/change-password", "/api/auth/logout", "/api/auth/refresh"}

ip_limiter = SlidingWindow(get_settings().login_ip_per_minute, 60)
_hasher = Argon2PasswordHasher()
_secrets = TokenSecrets()
_access = JwtAccessTokens()

# what lives outside the module (the academic context's classes, the seed data) is wired by the composition root
_class_directory: Callable[[Session], ClassDirectory] | None = None
_org_seeder: Callable[[Session], OrgSeeder] | None = None


def register_class_directory(factory: Callable[[Session], ClassDirectory]) -> None:
    global _class_directory
    _class_directory = factory


def register_org_seeder(factory: Callable[[Session], OrgSeeder]) -> None:
    global _org_seeder
    _org_seeder = factory


def _classes(db: Session) -> ClassDirectory:
    if _class_directory is None:
        raise RuntimeError("no class directory registered")
    return _class_directory(db)


def _seeder(db: Session) -> OrgSeeder:
    if _org_seeder is None:
        raise RuntimeError("no org seeder registered")
    return _org_seeder(db)


def _policy() -> AuthPolicy:
    s = get_settings()
    return AuthPolicy(refresh_token_days=s.refresh_token_days, login_max_failures=s.login_max_failures,
                      login_lock_minutes=s.login_lock_minutes)


def _issuer(db: Session) -> SessionIssuer:
    return SessionIssuer(SqlOrganizationRepository(db), SqlMembershipRepository(db), SqlRefreshTokenRepository(db), _secrets, _access,
                         _policy())


def identity_api(db: Session) -> IdentityApi:
    """The identity context for another context (through the composition root), on the caller's session."""
    return IdentityApi(SqlUserRepository(db), SqlOrganizationRepository(db), SqlMembershipRepository(db))


# ------------------------------------------------------------------ who is calling


def principal(request: Request, db: Session) -> Principal:
    """(user, active org, role there) from the access cookie or a bearer token — cached for the request."""
    cached = getattr(request.state, "identity_principal", None)
    if cached is not None:
        return cached
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        header = request.headers.get("authorization", "")
        token = header[7:] if header.lower().startswith("bearer ") else None
    claims = _access.decode(token) if token else None
    if not claims:
        raise Unauthenticated()
    org_id = claims.get("org_id")
    handle = ResolvePrincipalHandler(SqlUserRepository(db), SqlOrganizationRepository(db), SqlMembershipRepository(db))
    p = handle(ResolvePrincipal(uuid.UUID(claims["sub"]), uuid.UUID(org_id) if org_id else None))
    request.state.identity_principal = p
    return p


def check_password_gate(request: Request, p: Principal) -> None:
    """A temporary password must be changed before anything else."""
    if p.user.must_change_password and request.url.path not in PASSWORD_CHANGE_ALLOWED:
        raise errors.password_change_required()


def actor_from_request(request: Request, db: Session) -> Actor:
    """Registered as the actor resolver by the composition root."""
    p = principal(request, db)
    check_password_gate(request, p)
    return Actor(user_id=p.user.id, org_id=p.org_id, role=p.role, is_super=p.user.is_super)


def super_actor(actor: Actor = Depends(current_actor)) -> Actor:
    """The platform admin (a global role: super_admin lives in the system org whatever org is open)."""
    if not actor.is_super:
        raise Forbidden()
    return actor


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")


# ------------------------------------------------------------------ sessions


def login(db: Session = Depends(get_db)) -> LoginHandler:
    return LoginHandler(SqlOrganizationRepository(db), SqlUserRepository(db), _hasher, _issuer(db), ip_limiter, _policy(), SqlUnitOfWork(db))


def refresh_session(db: Session = Depends(get_db)) -> RefreshSessionHandler:
    return RefreshSessionHandler(SqlRefreshTokenRepository(db), SqlUserRepository(db), SqlOrganizationRepository(db), _secrets, _issuer(db),
                                 SqlUnitOfWork(db))


def logout(db: Session = Depends(get_db)) -> LogoutHandler:
    return LogoutHandler(_issuer(db), SqlUnitOfWork(db))


def switch_org(db: Session = Depends(get_db)) -> SwitchOrgHandler:
    return SwitchOrgHandler(SqlUserRepository(db), SqlOrganizationRepository(db), SqlMembershipRepository(db), _issuer(db),
                            SqlAuditTrail(db), SqlUnitOfWork(db))


def change_password(db: Session = Depends(get_db)) -> ChangePasswordHandler:
    return ChangePasswordHandler(SqlUserRepository(db), _hasher, SqlUnitOfWork(db))


def get_me(db: Session = Depends(get_db)) -> GetMeHandler:
    return GetMeHandler(SqlUserRepository(db), SqlOrganizationRepository(db))


def my_orgs(db: Session = Depends(get_db)) -> MyOrgsHandler:
    return MyOrgsHandler(SqlUserRepository(db), SqlOrganizationRepository(db), SqlMembershipRepository(db))


# ------------------------------------------------------------------ users of the org


def search_users(db: Session = Depends(get_db)) -> SearchUsersHandler:
    return SearchUsersHandler(SqlUserReader(db))


def get_user(db: Session = Depends(get_db)) -> GetUserHandler:
    return GetUserHandler(SqlUserRepository(db), SqlMembershipRepository(db), SqlOrganizationRepository(db), SqlUserReader(db))


def create_user(db: Session = Depends(get_db)) -> CreateUserHandler:
    return CreateUserHandler(SqlUserRepository(db), SqlOrganizationRepository(db), _hasher, _secrets, SqlAuditTrail(db), SqlUnitOfWork(db))


def update_user(db: Session = Depends(get_db)) -> UpdateUserHandler:
    return UpdateUserHandler(SqlUserRepository(db), SqlMembershipRepository(db), SqlOrganizationRepository(db), SqlRefreshTokenRepository(db),
                             SqlUserReader(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def reset_password(db: Session = Depends(get_db)) -> ResetPasswordHandler:
    return ResetPasswordHandler(SqlUserRepository(db), SqlMembershipRepository(db), SqlRefreshTokenRepository(db), _hasher, _secrets,
                                SqlAuditTrail(db), SqlUnitOfWork(db))


def link_account(db: Session = Depends(get_db)) -> LinkAccountHandler:
    return LinkAccountHandler(SqlUserRepository(db), SqlOrganizationRepository(db), SqlMembershipRepository(db), SqlAuditTrail(db),
                              SqlUnitOfWork(db))


def unlink_account(db: Session = Depends(get_db)) -> UnlinkAccountHandler:
    return UnlinkAccountHandler(SqlUserRepository(db), SqlMembershipRepository(db), _classes(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def preview_import(db: Session = Depends(get_db)) -> PreviewImportHandler:
    return PreviewImportHandler(SqlUserRepository(db), FileSpreadsheetReader())


def commit_import(db: Session = Depends(get_db)) -> CommitImportHandler:
    return CommitImportHandler(SqlUserRepository(db), _classes(db), _hasher, _secrets, SqlAuditTrail(db), SqlUnitOfWork(db))


# ------------------------------------------------------------------ platform admin


def search_orgs(db: Session = Depends(get_db)) -> SearchOrgsHandler:
    return SearchOrgsHandler(SqlOrgReader(db))


def get_org(db: Session = Depends(get_db)) -> GetOrgHandler:
    return GetOrgHandler(SqlOrganizationRepository(db), SqlOrgReader(db))


def create_org(db: Session = Depends(get_db)) -> CreateOrgHandler:
    return CreateOrgHandler(SqlOrganizationRepository(db), SqlUserRepository(db), _seeder(db), _hasher, _secrets, SqlAuditTrail(db),
                            SqlUnitOfWork(db))


def update_org(db: Session = Depends(get_db)) -> UpdateOrgHandler:
    return UpdateOrgHandler(SqlOrganizationRepository(db), SqlOrgReader(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def change_org_status(db: Session = Depends(get_db)) -> ChangeOrgStatusHandler:
    return ChangeOrgStatusHandler(SqlOrganizationRepository(db), SqlRefreshTokenRepository(db), SqlAuditTrail(db), SqlUnitOfWork(db))


def delete_org(db: Session = Depends(get_db)) -> DeleteOrgHandler:
    return DeleteOrgHandler(SqlOrganizationRepository(db), SqlUserRepository(db), SqlRefreshTokenRepository(db), SqlAuditTrail(db),
                            SqlUnitOfWork(db))


def search_accounts(db: Session = Depends(get_db)) -> SearchAccountsHandler:
    return SearchAccountsHandler(SqlAccountReader(db))


def search_org_members(db: Session = Depends(get_db)) -> SearchOrgMembersHandler:
    return SearchOrgMembersHandler(SqlOrganizationRepository(db), SqlMembershipReader(db))


def search_user_memberships(db: Session = Depends(get_db)) -> SearchUserMembershipsHandler:
    return SearchUserMembershipsHandler(SqlUserRepository(db), SqlMembershipReader(db))


def add_membership(db: Session = Depends(get_db)) -> AddMembershipHandler:
    return AddMembershipHandler(SqlUserRepository(db), SqlOrganizationRepository(db), SqlMembershipRepository(db), SqlAuditTrail(db),
                                SqlUnitOfWork(db))


def update_membership(db: Session = Depends(get_db)) -> UpdateMembershipHandler:
    return UpdateMembershipHandler(SqlUserRepository(db), SqlOrganizationRepository(db), SqlMembershipRepository(db), SqlAuditTrail(db),
                                   SqlUnitOfWork(db))


def remove_membership(db: Session = Depends(get_db)) -> RemoveMembershipHandler:
    return RemoveMembershipHandler(SqlUserRepository(db), SqlOrganizationRepository(db), SqlMembershipRepository(db), _classes(db),
                                   SqlAuditTrail(db), SqlUnitOfWork(db))
