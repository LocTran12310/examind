from dataclasses import dataclass, field
import uuid

from app.modules.assessment.application.common import Clock, GradedAnswer, exam_rows, load_assignment, result_breakdown
from app.modules.assessment.domain.ports import AssignmentRepository, ExamRepository, QuestionBank
from app.modules.assessment.domain.services import attempt_rules
from app.modules.assessment.domain.services.scoring import scaled
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class TrialRun:
    assignment_id: uuid.UUID
    responses: dict[uuid.UUID, dict | None] = field(default_factory=dict)


class TrialRunHandler:
    """Whoever set the exam sits it themselves: the responses are graded in memory against the current keys and come
    back in exactly the shape of GET /attempts/{id}/result, so the screen that shows a student's result shows this one.

    Nothing is written — no attempt, no answer, no answer fact, no mastery, no event — and the handler is built with no
    UnitOfWork at all, so there is nothing to commit (exam-runner ADR-01). That is what keeps the answer to "does a
    teacher's trial move the class report?" a permanent no, instead of every report having to remember a filter."""

    def __init__(self, assignments: AssignmentRepository, exams: ExamRepository, bank: QuestionBank, clock: Clock):
        self.assignments, self.exams, self.bank, self.clock = assignments, exams, bank, clock

    def __call__(self, actor: Actor, query: TrialRun) -> dict:
        a = load_assignment(self.assignments, actor.org_id, query.assignment_id)
        exam = self.exams.get_any(a.exam_id)
        rows = exam_rows(self.exams, self.bank, a.exam_id)
        graded: dict[uuid.UUID, GradedAnswer] = {}
        score, max_score, needs_grading = 0.0, 0.0, False
        for eq, q in rows:
            # the same cleaning a save does; the paper is unshuffled, so the labels are the question's own
            response = attempt_rules.checked_response(q, attempt_rules.from_display(None, q, query.responses.get(q.id)))
            g = attempt_rules.graded(q, response, eq.points)
            graded[q.id] = GradedAnswer(key=q.answer, response=response, points=g.points, is_correct=g.is_correct)
            score += g.points or 0
            max_score += eq.points
            needs_grading = needs_grading or g.points is None
        items, sections, topics = result_breakdown(None, rows, self.bank.views(None, [q.id for _, q in rows]), graded)
        return {"id": None, "title": a.title, "status": "submitted", "submitted_at": self.clock(), "needs_grading": needs_grading,
                "tab_switches": 0, "score": round(score, 4), "max_score": round(max_score, 4),
                "score10": scaled(score, max_score, exam.scale_to), "hidden": False,
                "questions": items, "sections": sections, "topics": topics}
