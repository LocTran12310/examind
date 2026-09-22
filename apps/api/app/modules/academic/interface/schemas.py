from datetime import date, datetime
import uuid

from pydantic import BaseModel, Field

from app.shared.interface.search_schemas import SearchBody

# ------------------------------------------------------------------ school years


class TermIO(BaseModel):
    code: str
    name: str | None = None
    start_date: date
    end_date: date


class YearIn(BaseModel):
    code: str = Field(min_length=9, max_length=9)
    name: str | None = Field(default=None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    terms: list[TermIO] | None = None


class YearUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    terms: list[TermIO] | None = None


class YearOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    start_date: date
    end_date: date
    status: str
    terms: list[TermIO]
    class_count: int = 0


def year_out(v) -> YearOut:
    return YearOut(**{**vars(v), "terms": [TermIO(**vars(t)) for t in v.terms]})


class PreviewIn(BaseModel):
    target_code: str | None = None


class RolloverStudentIn(BaseModel):
    user_id: uuid.UUID
    action: str


class RolloverClassIn(BaseModel):
    source_class_id: uuid.UUID
    target_name: str | None = None
    students: list[RolloverStudentIn] = []


class CommitIn(BaseModel):
    target_code: str
    classes: list[RolloverClassIn]
    activate_target: bool = False


# ------------------------------------------------------------------ classes


class ClassOut(BaseModel):
    id: uuid.UUID
    name: str
    grade: int | None
    grade_id: uuid.UUID | None = None
    school_year: str
    school_year_id: uuid.UUID | None = None
    member_count: int = 0
    created_at: datetime


class MemberOut(BaseModel):
    """Same shape as a row of the users list."""
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


class ClassDetail(ClassOut):
    members: list[MemberOut] = []


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    school_year: str | None = None
    school_year_id: uuid.UUID | None = None
    grade: int | None = None
    grade_id: uuid.UUID | None = None


class ClassUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    school_year: str | None = None
    school_year_id: uuid.UUID | None = None
    grade: int | None = None
    grade_id: uuid.UUID | None = None


class MembersIn(BaseModel):
    user_ids: list[uuid.UUID]


class ClassSearchBody(SearchBody):
    """`school_year_id`: the year chosen in the header · `grade_id`: a khối of the structure tree."""
    school_year_id: uuid.UUID | None = None
    grade_id: uuid.UUID | None = None


# ------------------------------------------------------------------ structure


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


class GradeSearchBody(SearchBody):
    school_level_id: uuid.UUID | None = None


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
