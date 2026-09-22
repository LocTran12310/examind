from datetime import datetime
import uuid

from pydantic import BaseModel, Field


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


def user_out(u, class_ids=None, member=None) -> UserOut:
    """`member` = the user's OrganizationMember in the org being viewed (role/status there)."""
    home = member is None or member.organization_id == u.organization_id
    return UserOut(id=u.id, username=u.username, full_name=u.full_name, email=u.email, role=member.role if member else u.role,
                   is_active=u.is_active and (member.is_active if member else True), must_change_password=u.must_change_password,
                   last_login_at=u.last_login_at, created_at=u.created_at, class_ids=class_ids or [],
                   is_home=home, home_org_code=u.organization.code)
