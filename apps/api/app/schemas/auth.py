import uuid

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    org_code: str = Field(min_length=1, max_length=64)
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class OrgOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str


class MeOut(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str
    role: str  # role in the active org
    must_change_password: bool
    org: OrgOut  # the active org
    home_org: OrgOut
    is_super: bool = False


class MyOrgOut(OrgOut):
    role: str
    is_home: bool


class SwitchOrgIn(BaseModel):
    org_id: uuid.UUID


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


def me_out(user, org=None, role: str | None = None) -> MeOut:
    home = user.organization
    o = org or home
    return MeOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=role or user.role,
        must_change_password=user.must_change_password,
        org=OrgOut(id=o.id, code=o.code, name=o.name),
        home_org=OrgOut(id=home.id, code=home.code, name=home.name),
        is_super=user.role == "super_admin",
    )
