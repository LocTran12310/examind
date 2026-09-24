"""Steps several assessment use cases share: loading what the caller may see, an exam's questions with their bank
content, an assignment's students, and grading (submit, lazy close, answer facts)."""
from collections.abc import Callable
from datetime import datetime
import uuid

from app.modules.assessment.domain.entities import AnswerFact, Assignment, Attempt, AttemptAnswer, Exam, ExamQuestion
from app.modules.assessment.domain.ports import (
    AnswerFacts,
    AssignmentRepository,
    AttemptRepository,
    ExamRepository,
    FactListener,
    QuestionBank,
    Roster,
)
from app.modules.assessment.domain.services import attempt_rules
from app.modules.assessment.domain.value_objects import QuestionRef, Snapshot
from app.shared.application.actor import Actor
from app.shared.domain.errors import Conflict, NotFound

Clock = Callable[[], datetime]


def load_exam(exams: ExamRepository, org_id: uuid.UUID, exam_id: uuid.UUID) -> Exam:
    e = exams.get(org_id, exam_id)
    if e is None:
        raise NotFound("Không tìm thấy đề")
    return e


def guard_edit(exams: ExamRepository, exam: Exam) -> None:
    """An exam somebody already took is frozen (its attempts were graded against it)."""
    if exams.has_attempts(exam.id):
        raise Conflict("Đề đã có học sinh làm — hãy tạo bản sao để sửa", code="exam_in_use")


def load_assignment(assignments: AssignmentRepository, org_id: uuid.UUID, assignment_id: uuid.UUID) -> Assignment:
    a = assignments.get(org_id, assignment_id)
    if a is None:
        raise NotFound("Không tìm thấy bài được giao")
    return a


def load_attempt(attempts: AttemptRepository, actor: Actor, attempt_id: uuid.UUID) -> Attempt:
    """Staff see every attempt of the org, a student only their own."""
    att = attempts.get(actor.org_id, attempt_id)
    if att is None or (actor.role == "student" and att.student_id != actor.user_id):
        raise NotFound("Không tìm thấy bài làm")
    return att


def exam_rows(exams: ExamRepository, bank: QuestionBank, exam_id: uuid.UUID) -> list[tuple[ExamQuestion, QuestionRef]]:
    """The exam's questions by position with their bank content."""
    eqs = exams.questions(exam_id)
    refs = {q.id: q for q in bank.questions(None, [eq.question_id for eq in eqs])}
    return [(eq, refs[eq.question_id]) for eq in eqs if eq.question_id in refs]


def runner_question(att: Attempt | None, eq: ExamQuestion, q: QuestionRef, number: int, response: dict | None) -> dict:
    """One question as the runner shows it: the key, the truth flags and the solution stripped, MCQ options in the
    order of the sitting and relabelled A–D. A trial run's paper goes through this same function (exam-runner ADR-04)
    with `att` None — the exam's own order, nothing behind it; a second shape for staff is how a key starts leaking."""
    return {"id": q.id, "type": q.type, "stem": q.stem, "answer": None, "solution": "", "difficulty": q.difficulty, "grade": q.grade,
            "status": q.status,
            "options": [{k: v for k, v in o.items() if k != "is_true"} for o in attempt_rules.display_options(att, q)],
            "number": number, "section": eq.section, "points": eq.points,
            "response": attempt_rules.to_display(att, q, response)}


def students_of(assignments: AssignmentRepository, roster: Roster, a: Assignment) -> set[uuid.UUID]:
    """Targeted students, plus the active students (active accounts) of the targeted classes."""
    targets = assignments.targets(a.id)
    ids = {t.user_id for t in targets if t.user_id}
    class_ids = [t.class_id for t in targets if t.class_id]
    if class_ids:
        ids |= roster.students(a.organization_id, roster.class_members(a.organization_id, class_ids), active_accounts=True)
    return ids


class Grading:
    """Submitting an attempt: every question graded against its current key (kept with the answer), one answer fact
    per graded answer (with the student's school-year snapshot) and the facts reported in grading order."""

    def __init__(self, attempts: AttemptRepository, exams: ExamRepository, bank: QuestionBank, roster: Roster,
                 facts: AnswerFacts, listener: FactListener, clock: Clock):
        self.attempts, self.exams, self.bank, self.roster, self.facts, self.listener, self.clock = (
            attempts, exams, bank, roster, facts, listener, clock)
        self._snapshots: dict[uuid.UUID, Snapshot] = {}

    def questions(self, att: Attempt) -> list[tuple[ExamQuestion, QuestionRef]]:
        return attempt_rules.in_order(att, exam_rows(self.exams, self.bank, att.exam_id))

    def finalize_if_expired(self, att: Attempt) -> bool:
        if attempt_rules.expired(att, self.clock()):
            self.submit(att, auto=True)
            return True
        return False

    def submit(self, att: Attempt, auto: bool = False) -> Attempt:
        if att.status != "in_progress":
            return att
        rows = self.questions(att)
        classes = self.bank.classification([q.id for _, q in rows])
        answers, max_total = [], 0.0
        for eq, q in rows:
            ans = self.attempts.answer(att.id, q.id)
            if ans is None:
                ans = AttemptAnswer(attempt_id=att.id, question_id=q.id, response=None)
                self.attempts.add_answer(ans)
            attempt_rules.grade_answer(ans, q, eq.points)
            max_total += eq.points
            answers.append(ans)
            self.attempts.flush()
            self.record(att, q, ans, classes.get(q.id))
        attempt_rules.close(att, answers, max_total, self.clock(), auto)
        self.attempts.flush()
        return att

    def record(self, att: Attempt, q: QuestionRef, ans: AttemptAnswer,
               classification: tuple[str | None, list[uuid.UUID]] | None = None) -> None:
        """The answer's fact follows its points: replaced, or removed while it has none. A question nobody answered
        still scores 0 in the result but leaves no fact behind (learning-telemetry ADR-02)."""
        if ans.points is None or not ans.max_points or not attempt_rules.answered(ans):
            self.facts.replace(att.id, q.id, None)
            return
        if att.id not in self._snapshots:  # one lookup per attempt, not per question
            self._snapshots[att.id] = self.roster.snapshot(att.organization_id, att.student_id, att.submitted_at or self.clock())
        snap = self._snapshots[att.id]
        path, tag_ids = classification if classification is not None else self.bank.classification([q.id]).get(q.id, (None, []))
        first = not self.facts.earlier(att.student_id, q.id, att.id, att.started_at or self.clock())
        fact = AnswerFact(organization_id=att.organization_id, attempt_id=att.id, assignment_id=att.assignment_id, exam_id=att.exam_id,
                          student_id=att.student_id, question_id=q.id, topic_path=path, tag_ids=list(tag_ids), qtype=q.type,
                          difficulty=q.difficulty, points=ans.points, max_points=ans.max_points,
                          correct_ratio=round(ans.points / ans.max_points, 4), created_at=self.clock(),
                          school_year_id=snap.school_year_id, term_code=snap.term_code, class_ids=list(snap.class_ids),
                          seconds_spent=ans.seconds_spent, answered_at=ans.answered_at, first_attempt=first)
        self.facts.replace(att.id, q.id, fact)
        self.listener.recorded(fact)
