from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import load_assignment
from app.modules.assessment.domain.ports import AssignmentRepository, AttemptRepository
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict


@dataclass(frozen=True)
class DeleteAssignment:
    assignment_id: uuid.UUID


class DeleteAssignmentHandler:
    def __init__(self, assignments: AssignmentRepository, attempts: AttemptRepository, uow: UnitOfWork):
        self.assignments, self.attempts, self.uow = assignments, attempts, uow

    def __call__(self, actor: Actor, cmd: DeleteAssignment) -> None:
        a = load_assignment(self.assignments, actor.org_id, cmd.assignment_id)
        if self.attempts.count(a.id):
            raise Conflict("Đã có học sinh làm bài — không thể xóa, hãy đóng sớm", code="assignment_in_use")
        self.assignments.remove(a)
        self.uow.commit()
