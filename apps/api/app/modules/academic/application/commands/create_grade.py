from dataclasses import dataclass
import uuid

from app.modules.academic.application.commands._structure import check_grade
from app.modules.academic.application.common import require_admin
from app.modules.academic.application.dto import GradeView, grade_view
from app.modules.academic.domain.entities import Grade
from app.modules.academic.domain.ports import GradeRepository, LevelRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class CreateGrade:
    level: int
    school_level_id: uuid.UUID
    name: str | None = None  # empty = "Lớp N"


class CreateGradeHandler:
    def __init__(self, levels: LevelRepository, grades: GradeRepository, audit: AuditTrail, uow: UnitOfWork):
        self.levels, self.grades, self.audit, self.uow = levels, grades, audit, uow

    def __call__(self, actor: Actor, cmd: CreateGrade) -> GradeView:
        require_admin(actor)
        check_grade(self.levels, self.grades, actor.org_id, cmd.level, cmd.school_level_id)
        g = Grade(organization_id=actor.org_id, level=cmd.level, name=(cmd.name or "").strip() or f"Lớp {cmd.level}",
                  school_level_id=cmd.school_level_id)
        self.grades.add(g)
        self.audit.record(actor, actor.org_id, "grade.create", "grade", g.id, level=cmd.level)
        self.uow.commit()
        return grade_view(g)
