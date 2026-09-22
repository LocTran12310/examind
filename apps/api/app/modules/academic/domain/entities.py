"""Academic context: school years with their terms, the school structure (cấp học › khối) and classes."""
from dataclasses import dataclass, field
from datetime import date, datetime
import uuid

from app.shared.domain.ids import new_id

YEAR_STATUSES = ("planning", "active", "closed")
TERMS = (("hk1", "Học kỳ 1"), ("hk2", "Học kỳ 2"))
ENROLLMENT_STATUSES = ("active", "promoted", "retained", "transferred", "graduated")


@dataclass(eq=False)
class SchoolTerm:
    code: str
    name: str
    start_date: date
    end_date: date
    school_year_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=new_id)


@dataclass(eq=False)
class SchoolYear:
    """Năm học of one org; exactly one is active (school-years A-01)."""
    organization_id: uuid.UUID
    code: str
    name: str
    start_date: date
    end_date: date
    status: str = "planning"
    terms: list[SchoolTerm] = field(default_factory=list)
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None


@dataclass(eq=False)
class SchoolLevel:
    """Cấp học (THCS, THPT…) owned by an org; grades 'belong' to the level whose range contains them."""
    organization_id: uuid.UUID
    code: str
    name: str
    grade_from: int
    grade_to: int
    sort: int = 0
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None


@dataclass(eq=False)
class Grade:
    organization_id: uuid.UUID
    level: int
    name: str
    school_level_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=new_id)


@dataclass(eq=False)
class SchoolClass:
    organization_id: uuid.UUID
    name: str
    school_year: str  # "2026-2027" — cache of school_years.code
    grade: int | None = None  # cache of grades.level for bank/exam filters
    grade_id: uuid.UUID | None = None
    school_year_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None


@dataclass(eq=False)
class ClassMember:
    class_id: uuid.UUID
    user_id: uuid.UUID
    # enrollment (school-years A-05): active | promoted | retained | transferred | graduated
    status: str = "active"
    joined_at: datetime | None = None
    left_at: datetime | None = None
