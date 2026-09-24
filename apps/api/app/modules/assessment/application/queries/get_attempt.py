from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import Clock, Grading, load_attempt, runner_question
from app.modules.assessment.application.ports import ResultReader
from app.modules.assessment.domain.ports import AssignmentRepository, AttemptRepository, ExamRepository
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class GetAttempt:
    attempt_id: uuid.UUID


class GetAttemptHandler:
    """What the runner shows: the questions in the attempt's order without keys or solutions, shuffled MCQ options
    relabelled A–D, the saved responses, the deadline and the server's time. An expired attempt is closed first."""

    def __init__(self, attempts: AttemptRepository, assignments: AssignmentRepository, exams: ExamRepository, grading: Grading,
                 people: ResultReader, clock: Clock, uow: UnitOfWork):
        self.attempts, self.assignments, self.exams, self.grading, self.people, self.clock, self.uow = (
            attempts, assignments, exams, grading, people, clock, uow)

    def __call__(self, actor: Actor, query: GetAttempt) -> dict:
        att = load_attempt(self.attempts, actor, query.attempt_id)
        if self.grading.finalize_if_expired(att):
            self.uow.commit()
        a = self.assignments.get_any(att.assignment_id) if att.assignment_id else None
        exam = self.exams.get_any(att.exam_id)
        answers = {x.question_id: x for x in self.attempts.answers(att.id)}
        questions = [runner_question(att, eq, q, i, (answers[q.id].response if q.id in answers else None))
                     for i, (eq, q) in enumerate(self.grading.questions(att), start=1)]
        student = self.people.people({att.student_id}).get(att.student_id)
        return {"id": att.id, "title": a.title if a else exam.title, "status": att.status, "started_at": att.started_at,
                "deadline_at": att.deadline_at, "submitted_at": att.submitted_at, "server_now": self.clock(), "tab_switches": att.tab_switches,
                "student": {"id": student.id, "full_name": student.full_name, "username": student.username} if student else None,
                "assignment_id": att.assignment_id, "questions": questions}
