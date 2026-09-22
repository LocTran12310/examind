from dataclasses import dataclass
import uuid

from app.modules.academic.application.commands._structure import check_grade
from app.modules.academic.application.common import load_grade, require_admin
from app.modules.academic.application.dto import GradeView, grade_view
from app.modules.academic.domain.ports import ClassRepository, GradeRepository, LevelRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class UpdateGrade:
    grade_id: uuid.UUID
    level: int | None = None
    name: str | None = None
    school_level_id: uuid.UUID | None = None


class UpdateGradeHandler:
    """Renumbering a grade keeps the classes' grade number in step (A-03)."""

    def __init__(self, levels: LevelRepository, grades: GradeRepository, classes: ClassRepository, audit: AuditTrail, uow: UnitOfWork):
        self.levels, self.grades, self.classes, self.audit, self.uow = levels, grades, classes, audit, uow

    def __call__(self, actor: Actor, cmd: UpdateGrade) -> GradeView:
        require_admin(actor)
        g = load_grade(self.grades, actor.org_id, cmd.grade_id)
        new_level = cmd.level if cmd.level is not None else g.level
        new_parent = cmd.school_level_id or g.school_level_id
        check_grade(self.levels, self.grades, actor.org_id, new_level, new_parent, g.id)
        if new_level != g.level:
            for c in self.classes.with_grade(g.id):
                c.grade = new_level
        g.level, g.school_level_id = new_level, new_parent
        if cmd.name:
            g.name = cmd.name.strip()
        self.audit.record(actor, actor.org_id, "grade.update", "grade", g.id)
        self.uow.commit()
        return grade_view(g)
