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
    role: str
    must_change_password: bool
    org: OrgOut


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


def me_out(user) -> MeOut:
    o = user.organization
    return MeOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        must_change_password=user.must_change_password,
        org=OrgOut(id=o.id, code=o.code, name=o.name),
    )
