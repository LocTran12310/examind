import uuid

from pydantic import BaseModel


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


def membership_out(m, user, org) -> MembershipOut:
    return MembershipOut(user_id=user.id, username=user.username, full_name=user.full_name, home_org_code=user.organization.code,
                         org_id=org.id, org_code=org.code, org_name=org.name, role=m.role, is_active=m.is_active,
                         is_home=user.organization_id == org.id)
