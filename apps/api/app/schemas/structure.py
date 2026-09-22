import uuid

from pydantic import BaseModel, Field


class LevelIn(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    grade_from: int = Field(ge=1, le=12)
    grade_to: int = Field(ge=1, le=12)
    sort: int = 0


class LevelUpdate(BaseModel):
    code: str | None = Field(default=None, max_length=20)
    name: str | None = Field(default=None, max_length=100)
    grade_from: int | None = Field(default=None, ge=1, le=12)
    grade_to: int | None = Field(default=None, ge=1, le=12)
    sort: int | None = None


class LevelOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    grade_from: int
    grade_to: int
    sort: int
    grade_count: int = 0


class GradeIn(BaseModel):
    level: int = Field(ge=1, le=12)
    name: str | None = Field(default=None, max_length=50)
    school_level_id: uuid.UUID


class GradeUpdate(BaseModel):
    level: int | None = Field(default=None, ge=1, le=12)
    name: str | None = Field(default=None, max_length=50)
    school_level_id: uuid.UUID | None = None


class GradeOut(BaseModel):
    id: uuid.UUID
    level: int
    name: str
    school_level_id: uuid.UUID | None
    class_count: int = 0


class TreeClass(BaseModel):
    id: uuid.UUID
    name: str
    school_year: str
    member_count: int


class TreeGrade(BaseModel):
    id: uuid.UUID
    level: int
    name: str
    class_count: int
    student_count: int
    classes: list[TreeClass]


class TreeLevel(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    grade_from: int
    grade_to: int
    class_count: int
    student_count: int
    grades: list[TreeGrade]


class StructureOut(BaseModel):
    levels: list[TreeLevel]
    unassigned: list[TreeClass]
