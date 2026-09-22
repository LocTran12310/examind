from dataclasses import dataclass
from datetime import datetime
import uuid

from app.modules.assessment.domain.entities import Assignment, AssignmentTarget
from app.modules.assessment.domain.ports import AssignmentRepository
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class AssignPersonalExam:
    organization_id: uuid.UUID
    exam_id: uuid.UUID
    student_id: uuid.UUID
    title: str
    open_at: datetime
    close_at: datetime
    duration_minutes: int
    created_by: uuid.UUID | None


class AssignPersonalExamHandler:
    """A personal review exam given to its student: one attempt, results after submitting; flushed with the caller's
    transaction (the caller checked the window and the duration)."""

    def __init__(self, assignments: AssignmentRepository, uow: UnitOfWork):
        self.assignments, self.uow = assignments, uow

    def __call__(self, cmd: AssignPersonalExam) -> uuid.UUID:
        a = Assignment(organization_id=cmd.organization_id, exam_id=cmd.exam_id, title=cmd.title, open_at=cmd.open_at,
                       close_at=cmd.close_at, duration_minutes=cmd.duration_minutes, max_attempts=1, results_policy="after_submit",
                       created_by=cmd.created_by)
        self.assignments.add(a, [AssignmentTarget(assignment_id=a.id, user_id=cmd.student_id)])
        self.uow.flush()
        return a.id
