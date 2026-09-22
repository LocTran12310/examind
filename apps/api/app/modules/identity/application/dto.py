from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.modules.identity.domain.entities import Membership, Organization, User


@dataclass(frozen=True)
class OrgRef:
    id: uuid.UUID
    code: str
    name: str


def org_ref(o: Organization) -> OrgRef:
    return OrgRef(o.id, o.code, o.name)


@dataclass(frozen=True)
class MeView:
    """The signed-in account in its active org."""
    id: uuid.UUID
    username: str
    full_name: str
    role: str  # role in the active org
    must_change_password: bool
    org: OrgRef  # the active org
    home_org: OrgRef
    is_super: bool = False


def me_view(user: User, home: Organization, org: Organization | None = None, role: str | None = None) -> MeView:
    return MeView(id=user.id, username=user.username, full_name=user.full_name, role=role or user.role,
                  must_change_password=user.must_change_password, org=org_ref(org or home), home_org=org_ref(home),
                  is_super=user.is_super)


@dataclass(frozen=True)
class SessionView:
    """A new session: the cookies to set and who is now signed in."""
    access_token: str
    refresh_token: str
    me: MeView


@dataclass(frozen=True)
class Principal:
    """The authenticated account, the org its token opens and its role there (re-checked on every request)."""
    user: User
    org_id: uuid.UUID
    role: str


@dataclass(frozen=True)
class MyOrgView:
    id: uuid.UUID
    code: str
    name: str
    role: str
    is_home: bool


@dataclass(frozen=True)
class UserView:
    """An account as seen from one org: role and status there."""
    id: uuid.UUID
    username: str
    full_name: str
    email: str | None
    role: str
    is_active: bool
    must_change_password: bool
    last_login_at: datetime | None
    created_at: datetime
    class_ids: list[uuid.UUID] = field(default_factory=list)
    is_home: bool = True
    home_org_code: str | None = None


def user_view(u: User, home_org_code: str, member: Membership | None = None, class_ids: list[uuid.UUID] | None = None) -> UserView:
    """`member` = the user's membership in the org being viewed (role/status there)."""
    home = member is None or member.organization_id == u.organization_id
    return UserView(id=u.id, username=u.username, full_name=u.full_name, email=u.email, role=member.role if member else u.role,
                    is_active=u.is_active and (member.is_active if member else True), must_change_password=u.must_change_password,
                    last_login_at=u.last_login_at, created_at=u.created_at, class_ids=class_ids or [], is_home=home,
                    home_org_code=home_org_code)


@dataclass(frozen=True)
class CreatedUser:
    user: UserView
    temp_password: str | None


@dataclass(frozen=True)
class Credential:
    user_id: uuid.UUID
    username: str
    full_name: str
    temp_password: str


@dataclass(frozen=True)
class OrgView:
    id: uuid.UUID
    code: str
    name: str
    status: str
    is_system: bool
    user_count: int
    created_at: datetime
    deleted_at: datetime | None


def org_view(o: Organization, user_count: int = 0) -> OrgView:
    return OrgView(id=o.id, code=o.code, name=o.name, status=o.status, is_system=o.is_system, user_count=user_count or 0,
                   created_at=o.created_at, deleted_at=o.deleted_at)


@dataclass(frozen=True)
class OrgCreated:
    org: OrgView
    admin_username: str
    temp_password: str


@dataclass(frozen=True)
class MembershipView:
    """A (user, org) membership, seen from either side (school-years ADR-04)."""
    user_id: uuid.UUID
    username: str
    full_name: str
    home_org_code: str
    org_id: uuid.UUID
    org_code: str
    org_name: str
    role: str
    is_active: bool
    is_home: bool


@dataclass(frozen=True)
class AccountView:
    id: uuid.UUID
    username: str
    full_name: str
    home_org_code: str
    home_org_name: str
    is_active: bool
    org_count: int


@dataclass(frozen=True)
class ImportPreview:
    rows: list[dict]
    valid_count: int
    error_count: int
