from dataclasses import dataclass
import uuid

from app.modules.academic.application.common import audit_class, load_class, resolve_grade, year_of_class
from app.modules.academic.application.dto import ClassView, class_view
from app.modules.academic.domain.ports import ClassRepository, GradeRepository, SchoolYearRepository
from app.modules.academic.domain.services.structure import check_class
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.calendar import BusinessCalendar
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict


@dataclass(frozen=True)
class UpdateClass:
    class_id: uuid.UUID
    name: str | None = None
    school_year: str | None = None
    grade: int | None = None
    grade_id: uuid.UUID | None = None
    school_year_id: uuid.UUID | None = None


class UpdateClassHandler:
    """A class of a closed year stays editable; the history records the change with the closed-year flag."""

    def __init__(self, years: SchoolYearRepository, classes: ClassRepository, grades: GradeRepository, audit: AuditTrail,
                 cal: BusinessCalendar, uow: UnitOfWork):
        self.years, self.classes, self.grades, self.audit, self.cal, self.uow = years, classes, grades, audit, cal, uow

    def __call__(self, actor: Actor, cmd: UpdateClass) -> ClassView:
        c = load_class(self.classes, actor.org_id, cmd.class_id)
        before = {"name": c.name, "school_year": c.school_year, "grade": c.grade}
        school_year, grade = cmd.school_year, cmd.grade
        if cmd.school_year or cmd.school_year_id:
            y = year_of_class(self.years, self.audit, self.cal, actor, cmd.school_year, cmd.school_year_id)
            school_year = y.code
            c.school_year_id = y.id
        g = resolve_grade(self.grades, actor.org_id, cmd.grade_id, grade) if (cmd.grade_id or grade is not None) else None
        if g is not None:
            grade = g.level
        new_name = cmd.name.strip() if cmd.name is not None else c.name
        new_year = school_year or c.school_year
        check_class(new_name, new_year, grade if grade is not None else c.grade)
        if (new_name, new_year) != (c.name, c.school_year) and self.classes.find(actor.org_id, new_name, new_year, exclude_id=c.id):
            raise Conflict("Lớp đã tồn tại trong năm học này", "name")
        c.name, c.school_year = new_name, new_year
        if grade is not None:
            c.grade = grade
            c.grade_id = g.id if g else None
        after = {"name": c.name, "school_year": c.school_year, "grade": c.grade}
        audit_class(self.audit, self.years, actor, "class.update", c, changes={k: [before[k], after[k]] for k in after if before[k] != after[k]})
        self.uow.commit()
        return class_view(c)
