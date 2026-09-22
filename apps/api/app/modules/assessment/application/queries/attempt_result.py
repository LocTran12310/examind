from dataclasses import dataclass
import uuid

from app.modules.assessment.application.common import Clock, Grading, load_attempt
from app.modules.assessment.domain.entities import STAFF_ROLES
from app.modules.assessment.domain.ports import AssignmentRepository, AttemptRepository, ExamRepository, QuestionBank
from app.modules.assessment.domain.services import assignment_rules, attempt_rules
from app.modules.assessment.domain.services.scoring import scaled
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork

UNCLASSIFIED = "Chưa phân loại"


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
        views = self.bank.views(None, [q.id for _, q in rows])
        items, by_section, by_topic = [], {}, {}
        for i, (eq, q) in enumerate(rows, start=1):
            ans = answers.get(q.id)
            item = dict(views[q.id])
            item["options"] = attempt_rules.display_options(att, q)
            key = ans.key_snapshot if ans and ans.key_snapshot is not None else q.answer  # the key used for grading (ADR-03)
            item["answer"] = attempt_rules.to_display(att, q, key)
            item.update({"number": i, "section": eq.section, "response": attempt_rules.to_display(att, q, ans.response) if ans else None,
                         "points": ans.points if ans else 0, "max_points": eq.points, "is_correct": ans.is_correct if ans else False,
                         "comment": ans.comment if ans else None})
            items.append(item)
            s = by_section.setdefault(eq.section, {"section": eq.section, "points": 0.0, "max_points": 0.0})
            s["points"] += item["points"] or 0
            s["max_points"] += eq.points
            topic = next((t for t in views[q.id].get("topics", []) if t["is_primary"]), None)
            name = topic["name"] if topic else UNCLASSIFIED
            t = by_topic.setdefault(name, {"topic": name, "points": 0.0, "max_points": 0.0, "count": 0})
            t["points"] += item["points"] or 0
            t["max_points"] += eq.points
            t["count"] += 1
        topics = sorted(by_topic.values(), key=lambda t: (t["points"] / t["max_points"]) if t["max_points"] else 1)
        return {**base, **score, "hidden": False, "questions": items, "sections": list(by_section.values()), "topics": topics}
