from datetime import datetime
import uuid

from pydantic import BaseModel, Field


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


class AdminCredential(BaseModel):
    username: str
    temp_password: str


class OrgCreated(BaseModel):
    org: OrgOut
    admin: AdminCredential
