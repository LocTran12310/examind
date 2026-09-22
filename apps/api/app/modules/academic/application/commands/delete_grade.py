from dataclasses import dataclass
import uuid

from app.modules.academic.application.common import load_grade, require_admin
from app.modules.academic.domain.ports import GradeRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict


@dataclass(frozen=True)
class DeleteGrade:
    grade_id: uuid.UUID


class DeleteGradeHandler:
    def __init__(self, grades: GradeRepository, audit: AuditTrail, uow: UnitOfWork):
        self.grades, self.audit, self.uow = grades, audit, uow

    def __call__(self, actor: Actor, cmd: DeleteGrade) -> None:
        require_admin(actor)
        g = load_grade(self.grades, actor.org_id, cmd.grade_id)
        n = self.grades.class_count(g.id)
        if n:
            raise Conflict(f"Khối còn {n} lớp", code="in_use")
        self.grades.remove(g)
        self.audit.record(actor, actor.org_id, "grade.delete", "grade", g.id, level=g.level)
        self.uow.commit()
