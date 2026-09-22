"""Rules several academic handlers share (loading in the org, the org-admin gate, the audit entries)."""
import uuid

from app.modules.academic.domain.entities import Grade, SchoolClass, SchoolLevel, SchoolYear
from app.modules.academic.domain.ports import ClassRepository, GradeRepository, LevelRepository, SchoolYearRepository
from app.modules.academic.domain.services import calendar
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.calendar import BusinessCalendar
from app.shared.domain.errors import Forbidden, Invalid, NotFound


def require_admin(actor: Actor) -> None:
    if actor.role != "org_admin":
        raise Forbidden()


def load_year(years: SchoolYearRepository, org_id: uuid.UUID, year_id: uuid.UUID) -> SchoolYear:
    y = years.get(org_id, year_id)
    if y is None:
        raise NotFound("Không tìm thấy năm học")
    return y


def load_class(classes: ClassRepository, org_id: uuid.UUID, class_id: uuid.UUID) -> SchoolClass:
    c = classes.get(org_id, class_id)
    if c is None:
        raise NotFound("Không tìm thấy lớp")
    return c


def load_level(levels: LevelRepository, org_id: uuid.UUID, level_id: uuid.UUID) -> SchoolLevel:
    lv = levels.get(org_id, level_id)
    if lv is None:
        raise NotFound("Không tìm thấy cấp học")
    return lv


def load_grade(grades: GradeRepository, org_id: uuid.UUID, grade_id: uuid.UUID) -> Grade:
    g = grades.get(org_id, grade_id)
    if g is None:
        raise NotFound("Không tìm thấy khối")
    return g


def audit_year(audit: AuditTrail, actor: Actor, y: SchoolYear, action: str, **data) -> None:
    audit.record(actor, actor.org_id, action, "school_year", y.id, code=y.code, closed_year=y.status == "closed", **data)


def ensure_year(years: SchoolYearRepository, audit: AuditTrail, cal: BusinessCalendar, org_id: uuid.UUID, code: str,
                actor: Actor | None = None) -> SchoolYear:
    """The org's year with this code, created (with HK1/HK2) when missing — classes and imports rely on it.
    A new year is active when it is the current one and the org has no active year."""
    code = calendar.check_code(code)
    y = years.by_code(org_id, code)
    if y is not None:
        return y
    status = "active" if code == calendar.current_code(cal.today()) and years.active(org_id) is None else "planning"
    y = calendar.new_year(org_id, code, status=status)
    years.add(y)
    if actor is not None:
        audit.record(actor, org_id, "year.create", "school_year", y.id, code=code)
    return y


def set_status(years: SchoolYearRepository, audit: AuditTrail, actor: Actor, y: SchoolYear, status: str) -> SchoolYear:
    """activate: this year becomes the only active one (the previous active year is closed); close; reopen → planning."""
    if status == "active":
        prev = years.active(actor.org_id)
        if prev is not None and prev.id != y.id:
            prev.status = "closed"
            years.flush()
            audit_year(audit, actor, prev, "year.close", reason="another year activated")
        y.status = "active"
        years.flush()
        audit_year(audit, actor, y, "year.activate")
    elif status == "closed":
        y.status = "closed"
        audit_year(audit, actor, y, "year.close")
    elif status == "planning":
        was = y.status
        y.status = "planning"
        audit_year(audit, actor, y, "year.reopen", was=was)
    else:
        raise Invalid("Trạng thái không hợp lệ", "status")
    return y


def audit_class(audit: AuditTrail, years: SchoolYearRepository, actor: Actor, action: str, c: SchoolClass, **data) -> None:
    y = years.get(actor.org_id, c.school_year_id) if c.school_year_id else None
    audit.record(actor, actor.org_id, action, "class", c.id, name=c.name, school_year=c.school_year,
                 closed_year=bool(y and y.status == "closed"), **data)


def year_of_class(years: SchoolYearRepository, audit: AuditTrail, cal: BusinessCalendar, actor: Actor,
                  school_year: str | None = None, school_year_id: uuid.UUID | None = None) -> SchoolYear:
    """The class's year from an id, a code (created on demand), or the org's active year (created when missing)."""
    if school_year_id:
        return load_year(years, actor.org_id, school_year_id)
    if school_year:
        calendar.check_code(school_year, "school_year")
        return ensure_year(years, audit, cal, actor.org_id, school_year, actor)
    return years.active(actor.org_id) or ensure_year(years, audit, cal, actor.org_id, calendar.current_code(cal.today()), actor)


def resolve_grade(grades: GradeRepository, org_id: uuid.UUID, grade_id: uuid.UUID | None = None, grade: int | None = None) -> Grade | None:
    """A class's grade from `grade_id`, or from a bare grade number (imports, old clients)."""
    if grade_id:
        return load_grade(grades, org_id, grade_id)
    if grade is not None:
        return grades.by_level(org_id, grade)
    return None
