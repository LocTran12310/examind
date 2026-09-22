from datetime import datetime
import uuid

from pydantic import BaseModel, Field

from app.schemas.users import UserOut


class ClassOut(BaseModel):
    id: uuid.UUID
    name: str
    grade: int | None
    grade_id: uuid.UUID | None = None
    school_year: str
    member_count: int = 0
    created_at: datetime


class ClassDetail(ClassOut):
    members: list[UserOut] = []


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    school_year: str | None = None
    grade: int | None = None
    grade_id: uuid.UUID | None = None


class ClassUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    school_year: str | None = None
    grade: int | None = None
    grade_id: uuid.UUID | None = None


class MembersIn(BaseModel):
    user_ids: list[uuid.UUID]


def class_out(c, count=0) -> ClassOut:
    return ClassOut(id=c.id, name=c.name, grade=c.grade, grade_id=c.grade_id, school_year=c.school_year, member_count=count, created_at=c.created_at)
