import uuid

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import now
from app.deps import OrgScope, org_scope
from app.models import Assignment, AttemptAnswer, User
from app.routers.documents import parsed_many
from app.schemas.questions import question_out
from app.services import attempts, scoring

router = APIRouter(prefix="/attempts", tags=["attempts"])


class AnswerIn(BaseModel):
    response: dict | None


class GradeIn(BaseModel):
    points: float
    comment: str | None = None


def _header(response: Response) -> None:
    response.headers["X-Server-Time"] = now().isoformat()


@router.get("/{attempt_id}")
def get_attempt(attempt_id: uuid.UUID, response: Response, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    att = attempts.get_for(db, scope, attempt_id)
    attempts.finalize_if_expired(db, att)
    _header(response)
    a = db.get(Assignment, att.assignment_id) if att.assignment_id else None
    exam = attempts.exam_of(db, att)
    answers = {x.question_id: x for x in db.scalars(select(AttemptAnswer).where(AttemptAnswer.attempt_id == att.id))}
    questions = []
    for i, (eq, q) in enumerate(attempts._questions(db, att), start=1):
        view = question_out(q, hide_answer=True).model_dump()
        view["options"] = [{k: v for k, v in o.items() if k != "is_true"} for o in attempts.display_options(att, q)]
        ans = answers.get(q.id)
        questions.append({**view, "number": i, "section": eq.section, "points": eq.points,
                          "response": attempts.to_display(att, q, ans.response) if ans else None})
    student = db.get(User, att.student_id)
    return {"id": att.id, "title": a.title if a else exam.title, "status": att.status, "started_at": att.started_at,
            "deadline_at": att.deadline_at, "submitted_at": att.submitted_at, "server_now": now(), "tab_switches": att.tab_switches,
            "student": {"id": student.id, "full_name": student.full_name, "username": student.username},
            "assignment_id": att.assignment_id, "questions": questions}


@router.put("/{attempt_id}/answers/{qid}")
def save_answer(attempt_id: uuid.UUID, qid: uuid.UUID, body: AnswerIn, response: Response, scope: OrgScope = Depends(org_scope),
                db: Session = Depends(get_db)):
    att = attempts.get_for(db, scope, attempt_id)
    ans = attempts.save_answer(db, scope, att, qid, body.response)
    _header(response)
    from app.models import Question

    return {"question_id": ans.question_id, "response": attempts.to_display(att, db.get(Question, qid), ans.response), "saved_at": ans.updated_at}


@router.post("/{attempt_id}/submit")
def submit(attempt_id: uuid.UUID, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    from app.core.errors import forbidden

    att = attempts.get_for(db, scope, attempt_id)
    if att.student_id != scope.user.id:
        raise forbidden()
    attempts.submit(db, att, auto=attempts.expired(att))
    return {"id": att.id, "status": att.status}


@router.post("/{attempt_id}/tab-switch")
def tab_switch(attempt_id: uuid.UUID, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    att = attempts.get_for(db, scope, attempt_id)
    return {"tab_switches": attempts.tab_switch(db, scope, att)}


@router.get("/{attempt_id}/result")
def result(attempt_id: uuid.UUID, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    att = attempts.get_for(db, scope, attempt_id)
    attempts.finalize_if_expired(db, att)
    a = db.get(Assignment, att.assignment_id) if att.assignment_id else None
    exam = attempts.exam_of(db, att)
    scale_to = float((exam.settings or {}).get("scale_to", 10))
    staff = scope.role in ("org_admin", "teacher")
    base = {"id": att.id, "title": a.title if a else exam.title, "status": att.status, "submitted_at": att.submitted_at,
            "needs_grading": att.needs_grading, "tab_switches": att.tab_switches}
    if att.status != "submitted":
        return {**base, "hidden": True, "reason": "Bài chưa nộp"}
    score = {"score": att.score, "max_score": att.max_score, "score10": scoring.scaled(att.score or 0, att.max_score or 0, scale_to)}
    if not staff and not attempts.results_visible(a, att):
        when = a.close_at if a and a.results_policy == "after_close" else None
        return {**base, **score, "hidden": True, "reason": "after_close" if when else "never", "available_at": when}
    rows = attempts._questions(db, att)
    answers = {x.question_id: x for x in db.scalars(select(AttemptAnswer).where(AttemptAnswer.attempt_id == att.id))}
    parsed = parsed_many(db, [q for _, q in rows])
    items, by_section, by_topic = [], {}, {}
    for i, ((eq, q), p) in enumerate(zip(rows, parsed), start=1):
        ans = answers.get(q.id)
        item = p.model_dump()
        item["options"] = attempts.display_options(att, q)
        key = ans.key_snapshot if ans and ans.key_snapshot is not None else q.answer  # the key used for grading (ADR-03)
        item["answer"] = attempts.to_display(att, q, key)
        item.update({"number": i, "section": eq.section, "response": attempts.to_display(att, q, ans.response) if ans else None,
                     "points": ans.points if ans else 0,
                     "max_points": eq.points, "is_correct": ans.is_correct if ans else False, "comment": ans.comment if ans else None})
        items.append(item)
        s = by_section.setdefault(eq.section, {"section": eq.section, "points": 0.0, "max_points": 0.0})
        s["points"] += item["points"] or 0
        s["max_points"] += eq.points
        topic = next((t for t in p.topics if t.is_primary), None)
        name = topic.name if topic else "Chưa phân loại"
        t = by_topic.setdefault(name, {"topic": name, "points": 0.0, "max_points": 0.0, "count": 0})
        t["points"] += item["points"] or 0
        t["max_points"] += eq.points
        t["count"] += 1
    topics = sorted(by_topic.values(), key=lambda t: (t["points"] / t["max_points"]) if t["max_points"] else 1)
    return {**base, **score, "hidden": False, "questions": items, "sections": list(by_section.values()), "topics": topics}


@router.patch("/{attempt_id}/answers/{qid}/grade")
def grade(attempt_id: uuid.UUID, qid: uuid.UUID, body: GradeIn, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    att = attempts.get_for(db, scope, attempt_id)
    att = attempts.grade_essay(db, scope, att, qid, body.points, body.comment)
    return {"score": att.score, "needs_grading": att.needs_grading}
