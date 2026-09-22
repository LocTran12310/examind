"""Identity context: organisations, accounts, their memberships and the sessions they open."""
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.shared.domain.ids import new_id

SYSTEM_ORG_CODE = "system"
ROLES = ("super_admin", "org_admin", "teacher", "student")
ORG_ROLES = ("org_admin", "teacher", "student")
STAFF_ROLES = ("org_admin", "teacher")


@dataclass(eq=False)
class Organization:
    code: str
    name: str
    status: str = "active"  # active | suspended
    is_system: bool = False
    settings: dict = field(default_factory=dict)
    deleted_at: datetime | None = None
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None

    @property
    def can_login(self) -> bool:
        return self.status == "active" and self.deleted_at is None


@dataclass(eq=False)
class User:
    """An account. `organization_id` is the home org (where the username lives); `role` mirrors the home membership (A-06)."""
    organization_id: uuid.UUID
    username: str
    password_hash: str
    full_name: str
    role: str
    email: str | None = None
    is_active: bool = True
    must_change_password: bool = False
    failed_logins: int = 0
    first_failed_at: datetime | None = None
    locked_until: datetime | None = None
    last_login_at: datetime | None = None
    last_org_id: uuid.UUID | None = None  # the org opened last (A-07)
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None

    @property
    def is_super(self) -> bool:
        return self.role == "super_admin"


@dataclass(eq=False)
class Membership:
    """A user's rights in one organisation; the home org always has one (school-structure-multi-org ADR-02)."""
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: str
    is_active: bool = True
    created_at: datetime | None = None


@dataclass(eq=False)
class RefreshToken:
    user_id: uuid.UUID
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None
