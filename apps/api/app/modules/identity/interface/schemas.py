"""Request/response bodies of the identity routes (field names unchanged: snake_case, ADR-07)."""
from datetime import datetime
import uuid

from pydantic import BaseModel, Field

from app.shared.interface.search_schemas import SearchBody

# ------------------------------------------------------------------ sessions


class LoginIn(BaseModel):
    org_code: str = Field(min_length=1, max_length=64)
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class OrgRefOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str


class MeOut(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str
    role: str  # role in the active org
    must_change_password: bool
    org: OrgRefOut  # the active org
    home_org: OrgRefOut
    is_super: bool = False


class MyOrgOut(OrgRefOut):
    role: str
    is_home: bool


class SwitchOrgIn(BaseModel):
    org_id: uuid.UUID


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


def me_out(v) -> MeOut:
    return MeOut(id=v.id, username=v.username, full_name=v.full_name, role=v.role, must_change_password=v.must_change_password,
                 org=OrgRefOut(id=v.org.id, code=v.org.code, name=v.org.name),
                 home_org=OrgRefOut(id=v.home_org.id, code=v.home_org.code, name=v.home_org.name), is_super=v.is_super)


# ------------------------------------------------------------------ users


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str
    email: str | None
    role: str
    is_active: bool
    must_change_password: bool
    last_login_at: datetime | None
    created_at: datetime
    class_ids: list[uuid.UUID] = []
    is_home: bool = True
    home_org_code: str | None = None


class UserSearchBody(SearchBody):
    """Filters: username, full_name, email (text) · role (enum) · is_active, must_change_password (bool) · created_at, last_login_at (date)."""
    class_id: uuid.UUID | None = None


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    role: str = "student"
    username: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=256)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=255)
    role: str | None = None
    is_active: bool | None = None


class LinkIn(BaseModel):
    org_code: str = Field(min_length=1, max_length=64)
    username: str = Field(min_length=1, max_length=64)
    role: str = "teacher"


class Credential(BaseModel):
    user_id: uuid.UUID
    username: str
    full_name: str
    temp_password: str


class UserCreated(BaseModel):
    user: UserOut
    temp_password: str | None


class ImportRowsIn(BaseModel):
    rows: list[dict]


def user_out(v) -> UserOut:
    return UserOut(id=v.id, username=v.username, full_name=v.full_name, email=v.email, role=v.role, is_active=v.is_active,
                   must_change_password=v.must_change_password, last_login_at=v.last_login_at, created_at=v.created_at,
                   class_ids=list(v.class_ids), is_home=v.is_home, home_org_code=v.home_org_code)


# ------------------------------------------------------------------ organisations (platform admin)


class OrgCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    admin_username: str = Field(default="admin", min_length=1, max_length=64)
    admin_full_name: str = Field(default="Quản trị trung tâm", min_length=1, max_length=200)


class OrgUpdate(BaseModel):
    code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=200)


class OrgOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    status: str
    is_system: bool
    user_count: int = 0
    created_at: datetime
    deleted_at: datetime | None


class OrgSearchBody(SearchBody):
    """Filters: code, name (text) · status (enum) · created_at (date)."""
    include_deleted: bool = False


class AdminCredential(BaseModel):
    username: str
    temp_password: str


class OrgCreated(BaseModel):
    org: OrgOut
    admin: AdminCredential


def org_out(v) -> OrgOut:
    return OrgOut(id=v.id, code=v.code, name=v.name, status=v.status, is_system=v.is_system, user_count=v.user_count,
                  created_at=v.created_at, deleted_at=v.deleted_at)


# ------------------------------------------------------------------ memberships (platform admin)


class MemberIn(BaseModel):
    org_code: str
    username: str
    role: str = "teacher"


class MembershipIn(BaseModel):
    org_id: uuid.UUID
    role: str = "teacher"


class MembershipPatch(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class MembershipOut(BaseModel):
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


class AccountOut(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str
    home_org_code: str
    home_org_name: str
    is_active: bool
    org_count: int


def membership_out(v) -> MembershipOut:
    return MembershipOut(**v.__dict__)


def account_out(v) -> AccountOut:
    return AccountOut(**v.__dict__)
