from dataclasses import dataclass, field
from datetime import date, datetime
import uuid


@dataclass(frozen=True)
class TermView:
    code: str
    name: str
    start_date: date
    end_date: date


@dataclass(frozen=True)
class YearView:
    id: uuid.UUID
    code: str
    name: str
    start_date: date
    end_date: date
    status: str
    terms: list[TermView]
    class_count: int = 0


def year_view(y, class_count: int = 0) -> YearView:
    return YearView(id=y.id, code=y.code, name=y.name, start_date=y.start_date, end_date=y.end_date, status=y.status,
                    terms=[TermView(t.code, t.name, t.start_date, t.end_date) for t in sorted(y.terms, key=lambda t: t.code)],
                    class_count=class_count or 0)


@dataclass(frozen=True)
class ClassView:
    id: uuid.UUID
    name: str
    grade: int | None
    grade_id: uuid.UUID | None
    school_year: str
    school_year_id: uuid.UUID | None
    created_at: datetime
    member_count: int = 0


def class_view(c, member_count: int = 0) -> ClassView:
    return ClassView(id=c.id, name=c.name, grade=c.grade, grade_id=c.grade_id, school_year=c.school_year, school_year_id=c.school_year_id,
                     created_at=c.created_at, member_count=member_count or 0)


@dataclass(frozen=True)
class MemberView:
    """A class member as the users list shows them (home account role, home org)."""
    id: uuid.UUID
    username: str
    full_name: str
    email: str | None
    role: str
    is_active: bool
    must_change_password: bool
    last_login_at: datetime | None
    created_at: datetime
    home_org_code: str | None = None


@dataclass(frozen=True)
class ClassDetailView:
    klass: ClassView
    members: list[MemberView] = field(default_factory=list)


@dataclass(frozen=True)
class LevelView:
    id: uuid.UUID
    code: str
    name: str
    grade_from: int
    grade_to: int
    sort: int
    grade_count: int = 0


def level_view(lv, grade_count: int = 0) -> LevelView:
    return LevelView(id=lv.id, code=lv.code, name=lv.name, grade_from=lv.grade_from, grade_to=lv.grade_to, sort=lv.sort,
                     grade_count=grade_count or 0)


@dataclass(frozen=True)
class GradeView:
    id: uuid.UUID
    level: int
    name: str
    school_level_id: uuid.UUID | None
    class_count: int = 0


def grade_view(g, class_count: int = 0) -> GradeView:
    return GradeView(id=g.id, level=g.level, name=g.name, school_level_id=g.school_level_id, class_count=class_count or 0)


@dataclass(frozen=True)
class RosterEntry:
    """A class member in the rollover plan."""
    user_id: uuid.UUID
    full_name: str
    username: str
    status: str
