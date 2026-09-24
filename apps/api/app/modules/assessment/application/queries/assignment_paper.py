from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import exam_rows, load_assignment, runner_question
from app.modules.assessment.domain.ports import AssignmentRepository, ExamRepository, QuestionBank
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class AssignmentPaper:
    assignment_id: uuid.UUID


class AssignmentPaperHandler:
    """The paper of an assignment as a student sees it — the exam's question order, keys and solutions stripped by the
    runner's own function (exam-runner ADR-04) — with nothing behind it: no attempt, so no timer, no deadline and no
    attempt id. What the person who set the exam needs to read it back before the window opens (AC-04)."""

    def __init__(self, assignments: AssignmentRepository, exams: ExamRepository, bank: QuestionBank):
        self.assignments, self.exams, self.bank = assignments, exams, bank

    def __call__(self, actor: Actor, query: AssignmentPaper) -> dict:
        a = load_assignment(self.assignments, actor.org_id, query.assignment_id)
        rows = exam_rows(self.exams, self.bank, a.exam_id)
        questions = [runner_question(None, eq, q, i, None) for i, (eq, q) in enumerate(rows, start=1)]
        return {"assignment_id": a.id, "exam_id": a.exam_id, "title": a.title,
                "max_score": round(sum(eq.points for eq, _ in rows), 4), "questions": questions}
