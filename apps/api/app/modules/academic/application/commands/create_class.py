from dataclasses import dataclass
import uuid

from app.modules.academic.application.common import audit_class, resolve_grade, year_of_class
from app.modules.academic.application.dto import ClassView, class_view
from app.modules.academic.domain.entities import SchoolClass
from app.modules.academic.domain.ports import ClassRepository, GradeRepository, SchoolYearRepository
from app.modules.academic.domain.services.structure import check_class
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.calendar import BusinessCalendar
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict


@dataclass(frozen=True)
class CreateClass:
    name: str
    school_year: str | None = None  # a code from an old client: the year is created on demand
    grade: int | None = None  # a bare grade number (imports): linked to the org's grade of that level
    grade_id: uuid.UUID | None = None
    school_year_id: uuid.UUID | None = None


def create_class(years: SchoolYearRepository, classes: ClassRepository, grades: GradeRepository, audit: AuditTrail,
                 cal: BusinessCalendar, actor: Actor, cmd: CreateClass) -> SchoolClass:
    """Without a year the class goes to the active year (created when the org has none)."""
    y = year_of_class(years, audit, cal, actor, cmd.school_year, cmd.school_year_id)
    grade = cmd.grade
    g = resolve_grade(grades, actor.org_id, cmd.grade_id, grade)
    if g is not None:
        grade = g.level
    check_class(cmd.name, y.code, grade)
    if classes.find(actor.org_id, cmd.name.strip(), y.code) is not None:
        raise Conflict("Lớp đã tồn tại trong năm học này", "name")
    c = SchoolClass(organization_id=actor.org_id, name=cmd.name.strip(), school_year=y.code, school_year_id=y.id, grade=grade,
                    grade_id=g.id if g else None)
    classes.add(c)
    audit_class(audit, years, actor, "class.create", c)
    return c


class CreateClassHandler:
    def __init__(self, years: SchoolYearRepository, classes: ClassRepository, grades: GradeRepository, audit: AuditTrail,
                 cal: BusinessCalendar, uow: UnitOfWork):
        self.years, self.classes, self.grades, self.audit, self.cal, self.uow = years, classes, grades, audit, cal, uow

    def __call__(self, actor: Actor, cmd: CreateClass) -> ClassView:
        c = create_class(self.years, self.classes, self.grades, self.audit, self.cal, actor, cmd)
        self.uow.commit()
        return class_view(c)
