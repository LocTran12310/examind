from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import Clock, GradedAnswer, Grading, load_attempt, result_breakdown
from app.modules.assessment.domain.entities import STAFF_ROLES
from app.modules.assessment.domain.ports import AssignmentRepository, AttemptRepository, ExamRepository, QuestionBank
from app.modules.assessment.domain.services import assignment_rules
from app.modules.assessment.domain.services.scoring import scaled
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class AttemptResult:
    attempt_id: uuid.UUID


class AttemptResultHandler:
    """The score on the exam's scale and, when the assignment's policy allows it (staff: always), every question with
    the response, the key used for grading, the solution, and totals per section and per primary topic (weakest first)."""

    def __init__(self, attempts: AttemptRepository, assignments: AssignmentRepository, exams: ExamRepository, bank: QuestionBank,
                 grading: Grading, clock: Clock, uow: UnitOfWork):
        self.attempts, self.assignments, self.exams, self.bank, self.grading, self.clock, self.uow = (
            attempts, assignments, exams, bank, grading, clock, uow)

    def __call__(self, actor: Actor, query: AttemptResult) -> dict:
        att = load_attempt(self.attempts, actor, query.attempt_id)
        if self.grading.finalize_if_expired(att):
            self.uow.commit()
        a = self.assignments.get_any(att.assignment_id) if att.assignment_id else None
        exam = self.exams.get_any(att.exam_id)
        base = {"id": att.id, "title": a.title if a else exam.title, "status": att.status, "submitted_at": att.submitted_at,
                "needs_grading": att.needs_grading, "tab_switches": att.tab_switches}
        if att.status != "submitted":
            return {**base, "hidden": True, "reason": "Bài chưa nộp"}
        score = {"score": att.score, "max_score": att.max_score, "score10": scaled(att.score or 0, att.max_score or 0, exam.scale_to)}
        if actor.role not in STAFF_ROLES and not assignment_rules.results_visible(a, att, self.clock()):
            when = a.close_at if a and a.results_policy == "after_close" else None
            return {**base, **score, "hidden": True, "reason": "after_close" if when else "never", "available_at": when}
        rows = self.grading.questions(att)
        answers = {x.question_id: x for x in self.attempts.answers(att.id)}
        graded = {q.id: GradedAnswer(key=ans.key_snapshot if ans.key_snapshot is not None else q.answer,  # the key it was graded against (ADR-03)
                                     response=ans.response, points=ans.points, is_correct=ans.is_correct, comment=ans.comment)
                  for _, q in rows if (ans := answers.get(q.id)) is not None}
        items, sections, topics = result_breakdown(att, rows, self.bank.views(None, [q.id for _, q in rows]), graded)
        return {**base, **score, "hidden": False, "questions": items, "sections": sections, "topics": topics}
