from dataclasses import dataclass
from datetime import datetime
import random
import uuid

from app.modules.assessment.application.common import Clock, Grading, exam_rows, load_assignment, students_of
from app.modules.assessment.domain.entities import Attempt
from app.modules.assessment.domain.ports import AssignmentRepository, AttemptRepository, ExamRepository, QuestionBank, Roster
from app.modules.assessment.domain.services import assignment_rules, attempt_rules
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict, Forbidden, NotFound


@dataclass(frozen=True)
class StartAttempt:
    assignment_id: uuid.UUID


def new_attempt(exams: ExamRepository, bank: QuestionBank, attempts: AttemptRepository, org_id: uuid.UUID, exam_id: uuid.UUID,
                student_id: uuid.UUID, deadline: datetime, assignment_id: uuid.UUID | None = None, shuffle_questions: bool = True,
                shuffle_options: bool = True, rng: random.Random | None = None) -> Attempt:
    """An attempt with its own question / option order; its maximum is the exam's total points."""
    rows = exam_rows(exams, bank, exam_id)
    order, option_orders = attempt_rules.orders(rows, shuffle_questions, shuffle_options, rng)
    att = Attempt(organization_id=org_id, assignment_id=assignment_id, exam_id=exam_id, student_id=student_id, deadline_at=deadline,
                  question_order=order, option_orders=option_orders, max_score=sum(eq.points for eq, _ in rows))
    attempts.add(att)
    return att


class StartAttemptHandler:
    """A targeted student in an open window: the attempt in progress is resumed, else a new one while attempts are
    left; its deadline is the time limit, never past the window's close (US-03, A-06)."""

    def __init__(self, assignments: AssignmentRepository, attempts: AttemptRepository, exams: ExamRepository, bank: QuestionBank,
                 roster: Roster, grading: Grading, clock: Clock, uow: UnitOfWork, rng: random.Random | None = None):
        self.assignments, self.attempts, self.exams, self.bank, self.roster = assignments, attempts, exams, bank, roster
        self.grading, self.clock, self.uow, self.rng = grading, clock, uow, rng

    def __call__(self, actor: Actor, cmd: StartAttempt) -> uuid.UUID:
        if actor.role != "student":
            raise Forbidden()
        a = load_assignment(self.assignments, actor.org_id, cmd.assignment_id)
        if actor.user_id not in students_of(self.assignments, self.roster, a):
            raise NotFound("Không tìm thấy bài được giao")
        assignment_rules.check_can_start(a, self.clock())
        current = self.attempts.current(a.id, actor.user_id)
        if current is not None:
            if self.grading.finalize_if_expired(current):
                raise Conflict("Lượt làm đã hết giờ", code="closed")
            return current.id
        assignment_rules.check_attempts_left(a, self.attempts.count(a.id, actor.user_id))
        att = new_attempt(self.exams, self.bank, self.attempts, actor.org_id, a.exam_id, actor.user_id,
                          assignment_rules.deadline(a, self.clock()), a.id, a.shuffle_questions, a.shuffle_options, self.rng)
        self.uow.commit()
        return att.id
