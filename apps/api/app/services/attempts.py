"""Attempts: server-timed taking, autosave, grading snapshot and answer facts (US-03, US-04, ADR-01..03)."""
from datetime import timedelta
import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.core.errors import AppError, forbidden, not_found
from app.core.security import now
from app.deps import OrgScope
from app.models import (AnswerFact, Assignment, Attempt, AttemptAnswer, Exam, ExamQuestion, Question, QuestionTag, QuestionTopic,
                        Topic)
from app.services import scoring

GRACE = timedelta(seconds=30)
MAX_TEXT = 20000


def get_for(db: Session, scope: OrgScope, attempt_id) -> Attempt:
    att = db.get(Attempt, attempt_id)
    if att is None or att.organization_id != scope.org_id:
        raise not_found("Không tìm thấy bài làm")
    if scope.role == "student" and att.student_id != scope.user.id:
        raise not_found("Không tìm thấy bài làm")
    return att


def expired(att: Attempt) -> bool:
    return att.status == "in_progress" and now() > att.deadline_at + GRACE


def finalize_if_expired(db: Session, att: Attempt) -> bool:
    if expired(att):
        submit(db, att, auto=True)
        return True
    return False


def _questions(db: Session, att: Attempt) -> list[tuple[ExamQuestion, Question]]:
    rows = {eq.question_id: (eq, q) for eq, q in db.execute(
        select(ExamQuestion, Question).join(Question, Question.id == ExamQuestion.question_id).where(ExamQuestion.exam_id == att.exam_id))}
    order = [uuid.UUID(i) for i in att.question_order] or [k for k, _ in sorted(rows.items(), key=lambda kv: kv[1][0].position)]
    return [rows[i] for i in order if i in rows]


def _ordered_options(att: Attempt, q: Question) -> list[dict]:
    order = (att.option_orders or {}).get(str(q.id))
    opts = q.options or []
    if not order:
        return opts
    by_label = {o["label"]: o for o in opts}
    return [by_label[l] for l in order if l in by_label]


DISPLAY = "ABCDEFGH"


def label_maps(att: Attempt, q: Question) -> tuple[dict, dict]:
    """Shuffled MCQ options are shown as A, B, C, D in their new order: (display→original, original→display)."""
    if q.type != "mcq":
        return {}, {}
    ordered = [o["label"] for o in _ordered_options(att, q)]
    to_orig = {DISPLAY[i]: lab for i, lab in enumerate(ordered)}
    return to_orig, {v: k for k, v in to_orig.items()}


def display_options(att: Attempt, q: Question) -> list[dict]:
    opts = _ordered_options(att, q)
    if q.type != "mcq":
        return opts
    return [{**o, "label": DISPLAY[i]} for i, o in enumerate(opts)]


def to_display(att: Attempt, q: Question, value: dict | None) -> dict | None:
    if q.type != "mcq" or not value or "key" not in value:
        return value
    return {**value, "key": label_maps(att, q)[1].get(value["key"], value["key"])}


def _check_response(q: Question, response) -> dict | None:
    if response is None:
        return None
    if not isinstance(response, dict):
        raise AppError("validation_error", "Câu trả lời không hợp lệ", 422)
    labels = {o.get("label") for o in q.options or []}
    if q.type == "mcq":
        if response.get("key") not in labels:
            raise AppError("validation_error", "Phương án không hợp lệ", 422)
        return {"key": response["key"]}
    if q.type == "true_false":
        return {k: v for k, v in response.items() if k in labels and isinstance(v, bool)}
    if q.type == "short_answer":
        return {"value": str(response.get("value", ""))[:100]}
    return {"text": str(response.get("text", ""))[:MAX_TEXT]}


def save_answer(db: Session, scope: OrgScope, att: Attempt, qid, response) -> AttemptAnswer:
    if att.student_id != scope.user.id:
        raise forbidden()
    if att.status != "in_progress" or finalize_if_expired(db, att):
        raise AppError("attempt_closed", "Bài làm đã kết thúc", 409)
    if str(qid) not in att.question_order:
        raise not_found("Câu hỏi không thuộc bài làm")
    q = db.get(Question, qid)
    if q.type == "mcq" and isinstance(response, dict) and "key" in response:
        response = {**response, "key": label_maps(att, q)[0].get(response["key"], "?")}
    clean = _check_response(q, response)
    ans = db.get(AttemptAnswer, (att.id, q.id))
    if ans is None:
        ans = AttemptAnswer(attempt_id=att.id, question_id=q.id)
        db.add(ans)
    ans.response = clean
    ans.updated_at = now()
    db.flush()
    return ans


def tab_switch(db: Session, scope: OrgScope, att: Attempt) -> int:
    if att.student_id != scope.user.id or att.status != "in_progress":
        return att.tab_switches
    db.execute(update(Attempt).where(Attempt.id == att.id).values(tab_switches=Attempt.tab_switches + 1))
    db.refresh(att)
    return att.tab_switches


def _primary_path(db: Session, qid) -> str | None:
    return db.scalar(select(Topic.path).join(QuestionTopic, QuestionTopic.topic_id == Topic.id)
                     .where(QuestionTopic.question_id == qid, QuestionTopic.is_primary.is_(True)))


def _fact(db: Session, att: Attempt, q: Question, ans: AttemptAnswer) -> None:
    db.execute(delete(AnswerFact).where(AnswerFact.attempt_id == att.id, AnswerFact.question_id == q.id))
    if ans.points is None or not ans.max_points:
        return
    db.add(AnswerFact(organization_id=att.organization_id, attempt_id=att.id, assignment_id=att.assignment_id, exam_id=att.exam_id,
                      student_id=att.student_id, question_id=q.id, topic_path=_primary_path(db, q.id),
                      tag_ids=list(db.scalars(select(QuestionTag.tag_id).where(QuestionTag.question_id == q.id))),
                      qtype=q.type, difficulty=q.difficulty, points=ans.points, max_points=ans.max_points,
                      correct_ratio=round(ans.points / ans.max_points, 4), created_at=now()))
    db.flush()
    from app.services import mastery

    fact = db.scalar(select(AnswerFact).where(AnswerFact.attempt_id == att.id, AnswerFact.question_id == q.id))
    mastery.apply_fact(db, fact)


def submit(db: Session, att: Attempt, auto: bool = False) -> Attempt:
    if att.status != "in_progress":
        return att
    total, max_total, pending = 0.0, 0.0, False
    for eq, q in _questions(db, att):
        ans = db.get(AttemptAnswer, (att.id, q.id))
        if ans is None:
            ans = AttemptAnswer(attempt_id=att.id, question_id=q.id, response=None)
            db.add(ans)
        g = scoring.grade(q.type, q.answer, ans.response, eq.points)
        ans.key_snapshot, ans.max_points, ans.points, ans.is_correct = q.answer, eq.points, g.points, g.is_correct
        if q.type == "essay" and not (ans.response or {}).get("text"):
            ans.points, ans.is_correct = 0.0, False  # nothing to grade
        max_total += eq.points
        if ans.points is None:
            pending = True
        else:
            total += ans.points
        db.flush()
        _fact(db, att, q, ans)
    att.status = "submitted"
    att.submitted_at = min(now(), att.deadline_at + GRACE) if auto else now()
    att.score, att.max_score, att.needs_grading = round(total, 4), round(max_total, 4), pending
    db.flush()
    return att


def sweep_expired(db: Session) -> int:
    rows = db.scalars(select(Attempt).where(Attempt.status == "in_progress", Attempt.deadline_at < now() - GRACE)).all()
    for att in rows:
        submit(db, att, auto=True)
    return len(rows)


def results_visible(a: Assignment | None, att: Attempt, score_only: bool = False) -> bool:
    if att.status != "submitted":
        return False
    if a is None or score_only:
        return True
    if a.results_policy == "after_submit":
        return True
    if a.results_policy == "after_close":
        return now() >= a.close_at
    return False


def grade_essay(db: Session, scope: OrgScope, att: Attempt, qid, points: float, comment: str | None) -> Attempt:
    if scope.role not in ("org_admin", "teacher"):
        raise forbidden()
    if att.status != "submitted":
        raise AppError("not_submitted", "Bài chưa nộp", 409)
    ans = db.get(AttemptAnswer, (att.id, qid))
    if ans is None:
        raise not_found("Không có câu trả lời")
    if not isinstance(points, (int, float)) or not 0 <= points <= ans.max_points:
        raise AppError("validation_error", f"Điểm từ 0 đến {ans.max_points}", 422, {"points": f"Điểm từ 0 đến {ans.max_points}"})
    ans.points, ans.comment, ans.graded_by = float(points), comment, scope.user.id
    ans.is_correct = points >= ans.max_points
    db.flush()
    _fact(db, att, db.get(Question, qid), ans)
    answers = db.scalars(select(AttemptAnswer).where(AttemptAnswer.attempt_id == att.id)).all()
    att.score = round(sum(a.points or 0 for a in answers), 4)
    att.needs_grading = any(a.points is None for a in answers)
    db.flush()
    return att


def exam_of(db: Session, att: Attempt) -> Exam:
    return db.get(Exam, att.exam_id)
