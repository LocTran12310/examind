"""Rules several identity handlers share: roles per org, the org a session opens, issuing a session."""
from collections.abc import Callable
from datetime import datetime, timedelta
import uuid

from app.modules.identity.application.dto import SessionView, me_view
from app.modules.identity.application.ports import AuthPolicy
from app.modules.identity.domain import errors
from app.modules.identity.domain.entities import SYSTEM_ORG_CODE, Membership, Organization, RefreshToken, User
from app.modules.identity.domain.ports import (
    AccessTokens,
    MembershipRepository,
    OrganizationRepository,
    RefreshTokenRepository,
    Secrets,
    UserRepository,
)
from app.modules.identity.domain.services.accounts import next_free_username, username_base
from app.shared.application.actor import Actor
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import Forbidden, NotFound

Clock = Callable[[], datetime]


def role_in(orgs: OrganizationRepository, members: MembershipRepository, user: User, org_id: uuid.UUID) -> str | None:
    """The user's role in `org_id`, or None when they may not work there. Super admins work in any org as org_admin (ADR-04)."""
    if user.is_super:
        org = orgs.get(org_id)
        if org is None or org.deleted_at is not None:
            return None
        return "super_admin" if org.is_system else "org_admin"
    m = members.get(user.id, org_id)
    return m.role if m is not None and m.is_active else None


def switchable_orgs(orgs: OrganizationRepository, members: MembershipRepository, user: User) -> list[tuple[Organization, str]]:
    """Organisations the user can switch to (active ones only), home first."""
    if user.is_super:
        return [(o, "super_admin" if o.is_system else "org_admin") for o in orgs.active() if o.can_login]
    out = [(o, r) for o, r in members.of_user(user.id) if o.can_login]
    return sorted(out, key=lambda x: x[0].id != user.organization_id)


def active_org(orgs: OrganizationRepository, members: MembershipRepository, user: User) -> tuple[Organization, str]:
    """The org a new session opens in: last used if still allowed, else home (A-07, A-11)."""
    for org_id in (user.last_org_id, user.organization_id):
        if org_id is None:
            continue
        org = orgs.get(org_id)
        role = role_in(orgs, members, user, org_id) if org is not None and org.can_login else None
        if role:
            return org, role
    raise errors.no_org_open()


def load_user(users: UserRepository, user_id: uuid.UUID) -> User:
    user = users.get(user_id)
    if user is None:
        raise errors.user_not_found()
    return user


def load_org(orgs: OrganizationRepository, org_id: uuid.UUID) -> Organization:
    org = orgs.get(org_id)
    if org is None:
        raise errors.org_not_found()
    return org


def load_member(users: UserRepository, members: MembershipRepository, org_id: uuid.UUID, user_id: uuid.UUID) -> tuple[User, Membership]:
    """A user of the org and their membership there (any status)."""
    user = users.get(user_id)
    m = members.get(user_id, org_id) if user is not None else None
    if user is None or m is None:
        raise errors.user_not_found()
    return user, m


def load_account(users: UserRepository, user_id: uuid.UUID) -> User:
    """An account the platform admin manages (super admins are not listed there)."""
    u = users.get(user_id)
    if u is None or u.is_super:
        raise NotFound("Không tìm thấy tài khoản")
    return u


def require_org_admin(actor: Actor) -> None:
    if actor.role != "org_admin":
        raise Forbidden()


def find_account(orgs: OrganizationRepository, users: UserRepository, org_code: str, username: str) -> User:
    """An active account by its home org code and username (linking an account of another org, A-10)."""
    code = (org_code or "").strip().lower()
    home = orgs.by_code(code) if code != SYSTEM_ORG_CODE else None
    user = users.by_username(home.id, (username or "").strip()) if home else None
    if user is None or not user.is_active:
        raise NotFound("Không tìm thấy tài khoản với mã tổ chức và tên đăng nhập này")
    return user


class SessionIssuer:
    """Issues the tokens of a session in its active org: the given one, else the last used, else home (ADR-03, A-07)."""

    def __init__(self, orgs: OrganizationRepository, members: MembershipRepository, tokens: RefreshTokenRepository,
                 secrets: Secrets, access: AccessTokens, policy: AuthPolicy, clock: Clock = utcnow):
        self.orgs, self.members, self.tokens, self.secrets, self.access = orgs, members, tokens, secrets, access
        self.policy, self.clock = policy, clock

    def issue(self, user: User, org: Organization | None = None, role: str | None = None) -> SessionView:
        if org is None or role is None:
            org, role = active_org(self.orgs, self.members, user)
        raw, digest = self.secrets.refresh_token()
        self.tokens.add(RefreshToken(user_id=user.id, token_hash=digest,
                                     expires_at=self.clock() + timedelta(days=self.policy.refresh_token_days)))
        access = self.access.issue(user.id, org.id, org.code, role)
        home = self.orgs.get(user.organization_id)
        return SessionView(access_token=access, refresh_token=raw, me=me_view(user, home, org, role))

    def end(self, raw_refresh: str | None) -> None:
        """Revoke the session's refresh token (logout, org switch)."""
        if raw_refresh:
            self.tokens.revoke(self.secrets.digest(raw_refresh), self.clock())


def generate_username(users: UserRepository, org_id: uuid.UUID, full_name: str, taken: set[str] | None = None) -> str:
    """From the full name without accents: "Lê An" → lean, then lean2, lean3… inside the org."""
    base = username_base(full_name)
    return next_free_username(base, users.usernames_like(org_id, base) | (taken or set()))


def home_code(orgs: OrganizationRepository, user: User) -> str:
    return load_org(orgs, user.organization_id).code
