"""Taking an exam: the attempt's question and option order, what a student sees (shuffled MCQ options relabelled
A, B, C, D), answer checks, the server-side time limit and grading on submit (exam-practice US-03, US-04, ADR-02, ADR-03)."""
from datetime import datetime, timedelta
import random
import uuid

from app.modules.assessment.domain.entities import Attempt, AttemptAnswer, ExamQuestion
from app.modules.assessment.domain.services import scoring
from app.modules.assessment.domain.value_objects import QuestionRef
from app.shared.domain.errors import Conflict, Invalid

GRACE = timedelta(seconds=30)
MAX_TEXT = 20000
MAX_SHORT = 100
DISPLAY = "ABCDEFGH"


def orders(rows: list[tuple[ExamQuestion, QuestionRef]], shuffle_questions: bool, shuffle_options: bool,
           rng: random.Random | None = None) -> tuple[list[str], dict[str, list[str]]]:
    """(question order, MCQ option orders): sections keep their order, questions are shuffled inside each;
    `rows` in exam position order."""
    rng = rng or random.Random()
    order: list[str] = []
    for section in dict.fromkeys(eq.section for eq, _ in rows):
        ids = [str(eq.question_id) for eq, _ in rows if eq.section == section]
        if shuffle_questions:
            rng.shuffle(ids)
        order += ids
    option_orders: dict[str, list[str]] = {}
    if shuffle_options:
        for eq, q in rows:
            if q.type == "mcq" and q.options:
                labels = [o["label"] for o in q.options]
                rng.shuffle(labels)
                option_orders[str(eq.question_id)] = labels
    return order, option_orders


def in_order(att: Attempt, rows: list[tuple[ExamQuestion, QuestionRef]]) -> list[tuple[ExamQuestion, QuestionRef]]:
    """The attempt's questions in its own order (exam position order when it has none)."""
    by_id = {eq.question_id: (eq, q) for eq, q in rows}
    order = [uuid.UUID(i) for i in att.question_order] or [eq.question_id for eq, _ in sorted(rows, key=lambda r: r[0].position)]
    return [by_id[i] for i in order if i in by_id]


def ordered_options(att: Attempt, q: QuestionRef) -> list[dict]:
    order = (att.option_orders or {}).get(str(q.id))
    opts = q.options or []
    if not order:
        return opts
    by_label = {o["label"]: o for o in opts}
    return [by_label[lab] for lab in order if lab in by_label]


def label_maps(att: Attempt, q: QuestionRef) -> tuple[dict, dict]:
    """Shuffled MCQ options are shown as A, B, C, D in their new order: (display→original, original→display)."""
    if q.type != "mcq":
        return {}, {}
    ordered = [o["label"] for o in ordered_options(att, q)]
    to_orig = {DISPLAY[i]: lab for i, lab in enumerate(ordered)}
    return to_orig, {v: k for k, v in to_orig.items()}


def display_options(att: Attempt, q: QuestionRef) -> list[dict]:
    opts = ordered_options(att, q)
    if q.type != "mcq":
        return opts
    return [{**o, "label": DISPLAY[i]} for i, o in enumerate(opts)]


def to_display(att: Attempt, q: QuestionRef, value: dict | None) -> dict | None:
    """A response or key in the labels the student sees."""
    if q.type != "mcq" or not value or "key" not in value:
        return value
    return {**value, "key": label_maps(att, q)[1].get(value["key"], value["key"])}


def from_display(att: Attempt, q: QuestionRef, response):
    """A student's MCQ choice back in the question's original labels ("?" for a label that is not shown)."""
    if q.type == "mcq" and isinstance(response, dict) and "key" in response:
        return {**response, "key": label_maps(att, q)[0].get(response["key"], "?")}
    return response


def checked_response(q: QuestionRef, response) -> dict | None:
    """What is stored of a response: only the known labels / a bounded text."""
    if response is None:
        return None
    if not isinstance(response, dict):
        raise Invalid("Câu trả lời không hợp lệ")
    labels = {o.get("label") for o in q.options or []}
    if q.type == "mcq":
        if response.get("key") not in labels:
            raise Invalid("Phương án không hợp lệ")
        return {"key": response["key"]}
    if q.type == "true_false":
        return {k: v for k, v in response.items() if k in labels and isinstance(v, bool)}
    if q.type == "short_answer":
        return {"value": str(response.get("value", ""))[:MAX_SHORT]}
    return {"text": str(response.get("text", ""))[:MAX_TEXT]}


def expired(att: Attempt, now: datetime) -> bool:
    return att.status == "in_progress" and now > att.deadline_at + GRACE


def grade_answer(ans: AttemptAnswer, q: QuestionRef, points: float) -> None:
    """Grade against the current key and keep that key with the answer; an empty essay scores 0."""
    g = scoring.grade(q.type, q.answer, ans.response, points)
    ans.key_snapshot, ans.max_points, ans.points, ans.is_correct = q.answer, points, g.points, g.is_correct
    if q.type == "essay" and not (ans.response or {}).get("text"):
        ans.points, ans.is_correct = 0.0, False  # nothing to grade


def close(att: Attempt, answers: list[AttemptAnswer], max_total: float, now: datetime, auto: bool) -> None:
    """Submitted: the total of the graded answers; an essay without points leaves it waiting for a teacher.
    An automatic close is dated at the deadline (plus grace) at the latest."""
    total = sum(a.points for a in answers if a.points is not None)
    att.status = "submitted"
    att.submitted_at = min(now, att.deadline_at + GRACE) if auto else now
    att.score, att.max_score = round(total, 4), round(max_total, 4)
    att.needs_grading = any(a.points is None for a in answers)


def check_open(att: Attempt) -> None:
    if att.status != "in_progress":
        raise Conflict("Bài làm đã kết thúc", code="attempt_closed")


def grade_essay(att: Attempt, ans: AttemptAnswer, points, comment: str | None, grader: uuid.UUID) -> None:
    if att.status != "submitted":
        raise Conflict("Bài chưa nộp", code="not_submitted")
    if not isinstance(points, (int, float)) or not 0 <= points <= ans.max_points:
        raise Invalid(f"Điểm từ 0 đến {ans.max_points}", "points")
    ans.points, ans.comment, ans.graded_by = float(points), comment, grader
    ans.is_correct = points >= ans.max_points


def regraded(att: Attempt, answers: list[AttemptAnswer]) -> None:
    att.score = round(sum(a.points or 0 for a in answers), 4)
    att.needs_grading = any(a.points is None for a in answers)
