from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.modules.assessment.application.common import load_exam
from app.modules.assessment.domain.entities import Assignment, AssignmentTarget
from app.modules.assessment.domain.ports import AssignmentRepository, ExamRepository, Roster
from app.modules.assessment.domain.services import assignment_rules
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Invalid


@dataclass(frozen=True)
class CreateAssignment:
    exam_id: uuid.UUID
    open_at: datetime
    close_at: datetime
    duration_minutes: int
    title: str | None = None
    max_attempts: int = 1
    shuffle_questions: bool = True
    shuffle_options: bool = True
    results_policy: str = "after_submit"
    class_ids: list[uuid.UUID] = field(default_factory=list)
    user_ids: list[uuid.UUID] = field(default_factory=list)


class CreateAssignmentHandler:
    """An exam with questions given to classes and/or students of the org for a window (US-02, A-05)."""

    def __init__(self, exams: ExamRepository, assignments: AssignmentRepository, roster: Roster, uow: UnitOfWork):
        self.exams, self.assignments, self.roster, self.uow = exams, assignments, roster, uow

    def __call__(self, actor: Actor, cmd: CreateAssignment) -> Assignment:
        exam = load_exam(self.exams, actor.org_id, cmd.exam_id)
        if not self.exams.questions(exam.id):
            raise Invalid("Đề chưa có câu hỏi", "exam_id")
        assignment_rules.check_window(cmd.open_at, cmd.close_at, cmd.duration_minutes, cmd.max_attempts, cmd.results_policy)
        if not cmd.class_ids and not cmd.user_ids:
            raise Invalid("Chọn ít nhất một lớp hoặc học sinh", "class_ids")
        if set(cmd.class_ids) - set(self.roster.class_names(actor.org_id, list(cmd.class_ids))):
            raise Invalid("Lớp không hợp lệ", "class_ids")
        if set(cmd.user_ids) - self.roster.students(actor.org_id, set(cmd.user_ids)):
            raise Invalid("Học sinh không hợp lệ", "user_ids")
        a = Assignment(organization_id=actor.org_id, exam_id=exam.id, title=(cmd.title or exam.title).strip(), open_at=cmd.open_at,
                       close_at=cmd.close_at, duration_minutes=cmd.duration_minutes, max_attempts=cmd.max_attempts,
                       shuffle_questions=cmd.shuffle_questions, shuffle_options=cmd.shuffle_options, results_policy=cmd.results_policy,
                       created_by=actor.user_id)
        targets = [AssignmentTarget(assignment_id=a.id, class_id=c) for c in cmd.class_ids]
        targets += [AssignmentTarget(assignment_id=a.id, user_id=u) for u in cmd.user_ids]
        self.assignments.add(a, targets)
        self.uow.commit()
        return a
