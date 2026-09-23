"""Review rules over a question's status (question-review ADR-03): queue groups, approval, rejection, restore,
content edits, the spot-check feedback that makes auto-approval stricter (A-07), and the one state a document is
read by (review-ux ADR-01)."""
from datetime import datetime
import uuid

from app.modules.bank.domain.entities import DIFFICULTIES, QUESTION_TYPES, Question
from app.modules.bank.domain.services.quality import blocking, blocking_manual, reevaluate, settle, triage_status
from app.modules.bank.domain.services.search_text import for_question
from app.shared.domain.errors import Conflict, Invalid

GROUP_ORDER = ["Nghi sai đáp án", "thiếu đáp án", "thiếu phương án", "không nhận ra phương án", "đáp án không khớp bảng đáp án",
               "đáp án không khớp định dạng", "OCR", "AI không phản hồi"]
SPOT_GROUP = "Kiểm tra ngẫu nhiên"
FLAGGED_GROUP = "Nghi sai đáp án"
SPOT_WINDOW, SPOT_FAILS, THRESHOLD_STEP, THRESHOLD_MAX = 20, 2, 0.05, 0.95
OPTION_KEYS = ("label", "content", "is_true")
WAITING = ("needs_review", "flagged")  # statuses that put a question back on a teacher's desk
REVIEW_STATES = ("pending", "in_progress", "done")
QUESTION_STATES = ("pending", "approved", "rejected", "duplicate", "all")


def waits_for_review(q: Question) -> bool:
    """Still on a teacher's desk: sent back, flagged, or drawn for the check sample and not looked at yet."""
    return q.status in WAITING or q.is_spot_pending


def pending_count(counts: dict[str, int], spot_pending: int) -> int:
    """How many questions of a document still wait for a human (ADR-01): the same rule as `waits_for_review`,
    counted per status."""
    return counts["needs_review"] + counts["flagged"] + spot_pending


def review_state(total: int, counts: dict[str, int], spot_pending: int) -> str:
    """The one state a document is read by (ADR-01): work left, nothing undecided, or decided but not finished."""
    if pending_count(counts, spot_pending) > 0:
        return "pending"
    decided = counts["approved"] + counts["rejected"] + counts["duplicate"] + counts["auto_approved"] - spot_pending
    return "done" if decided >= total else "in_progress"


def check_question_state(state: str) -> str:
    """The state a teacher filters a document's questions by (ADR-02); `all` is no filter."""
    if state not in QUESTION_STATES:
        raise Invalid("Trạng thái không hợp lệ", "state", code="bad_filter")
    return state


def group_of(q: Question) -> str:
    if q.is_spot_pending:
        return SPOT_GROUP
    for g in GROUP_ORDER:
        if g in (q.issues or []):
            return g
    b = blocking(q.issues or [])
    return b[0] if b else "Độ tin cậy thấp"


def queue_order(questions: list[Question]) -> list[Question]:
    """Problems first (by group), spot checks last; inside a group by part and number."""
    order = {g: i for i, g in enumerate(GROUP_ORDER)}

    def key(q: Question):
        g = group_of(q)
        return (1 if g == SPOT_GROUP else 0, order.get(g, len(order)), q.part or "", q.number or 0)

    return sorted(questions, key=key)


def check_type(qtype: str) -> str:
    if qtype not in QUESTION_TYPES:
        raise Invalid("Loại câu không hợp lệ", "type")
    return qtype


def check_difficulty(difficulty: str | None) -> str | None:
    if difficulty and difficulty not in DIFFICULTIES:
        raise Invalid("Mức độ không hợp lệ", "difficulty")
    return difficulty


def check_grade(grade: int | None, levels: set[int]) -> int | None:
    """A question's grade is one the org teaches (0 / None clears it)."""
    if grade and grade not in levels:
        raise Invalid("Lớp không hợp lệ", "grade")
    return grade


def valid_answer(qtype: str, options: list[dict], answer) -> dict | None:
    if answer in (None, {}, ""):
        return None
    if not isinstance(answer, dict):
        raise Invalid("Đáp án không hợp lệ", "answer")
    labels = {o.get("label") for o in options}
    if qtype == "mcq" and answer.get("key") not in labels:
        raise Invalid("Đáp án phải là một phương án", "answer")
    if qtype == "true_false":
        return {k: v for k, v in answer.items() if k in labels and isinstance(v, bool)}
    return answer


def blocking_message(q: Question, prefix: str = "Câu") -> str:
    return f"{prefix} còn lỗi: " + ", ".join(blocking_manual(q.issues or []))


def approve(q: Question, user_id: uuid.UUID, when: datetime) -> None:
    """A teacher approves: structural problems must be fixed first; flags that only asked for a look are settled."""
    if blocking_manual(q.issues or []):
        raise Conflict(blocking_message(q), code="has_blocking_issues")
    if q.status == "flagged":  # the teacher confirmed (or fixed) the key: remember when, to avoid re-flagging at once
        q.flag_evidence = {**(q.flag_evidence or {}), "dismissed": True, "answers_at_dismiss": (q.flag_evidence or {}).get("answers", 0)}
    settle(q)
    q.status, q.spot_check = "approved", False
    q.mark_reviewed(user_id, when)


def reject(q: Question, user_id: uuid.UUID, when: datetime) -> None:
    q.status, q.spot_check = "rejected", False
    q.mark_reviewed(user_id, when)


def restore(q: Question, threshold: float) -> None:
    if q.status not in ("rejected", "duplicate", "flagged"):
        raise Conflict("Chỉ khôi phục câu đã loại hoặc trùng", code="invalid_state")
    q.duplicate_of = None
    q.status = triage_status(q.confidence, q.issues or [], threshold)


def edit_content(q: Question, *, type: str | None = None, stem: str | None = None, solution: str | None = None,
                 options: list[dict] | None = None, answer: dict | None = None) -> bool:
    """Apply a teacher's content edit (None = unchanged). Returns whether the content changed; the status stays —
    the teacher approves explicitly."""
    changed = False
    if type is not None:
        q.type, changed = check_type(type), True
    if stem is not None:
        q.stem, changed = stem, True
    if solution is not None:
        q.solution, changed = solution, True
    if options is not None:
        q.options = [{k: v for k, v in o.items() if k in OPTION_KEYS} for o in options]
        changed = True
    if answer is not None:
        q.answer = valid_answer(q.type, q.options or [], answer)
        if q.type == "true_false" and q.answer:
            q.options = [{**o, "is_true": q.answer.get(o["label"])} for o in q.options]
        q.answer_source = "manual"
        changed = True
    if changed:
        reevaluate(q)
        q.search_text = for_question(q.stem, q.options)
    return changed


def spot_check_failed_by_edit(q: Question, user_id: uuid.UUID, when: datetime) -> None:
    """A teacher had to correct a spot-checked question: it counts as a failed check."""
    q.spot_check = False
    q.status = "approved" if not blocking(q.issues) else "needs_review"
    q.mark_reviewed(user_id, when)


def raised_threshold(recent_spot_actions: list[str], current: float) -> float | None:
    """Two failed spot checks in the last twenty make auto-approval stricter; None when nothing changes."""
    if sum(a == "spot_fail" for a in recent_spot_actions[:SPOT_WINDOW]) < SPOT_FAILS:
        return None
    new = min(THRESHOLD_MAX, round(current + THRESHOLD_STEP, 2))
    return new if new != current else None
