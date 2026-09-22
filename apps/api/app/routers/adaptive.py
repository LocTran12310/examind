import uuid

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import forbidden, not_found
from app.deps import OrgScope, org_scope
from app.models import Assignment, AssignmentTarget, Attempt, Exam, User
from app.deps import staff_scope
from app.services import adaptive, classes as class_service, mastery
from app.services.scoring import scaled

router = APIRouter(tags=["adaptive"])


@router.get("/me/mastery")
def my_mastery(scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    if scope.role != "student":
        raise forbidden()
    return mastery.rows_for(db, scope.org_id, scope.user.id)


@router.get("/students/{student_id}/mastery")
def student_mastery(student_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    from app.services.membership import member_ids

    if not member_ids(db, scope.org_id, {student_id}):
        raise not_found("Không tìm thấy học sinh")
    return mastery.rows_for(db, scope.org_id, student_id)


def weakest(rows: list[dict], n: int = 3) -> list[dict]:
    tracked = [r for r in rows if r["tracked"] and r["mastery"] is not None]
    return sorted(tracked, key=lambda r: r["mastery"])[:n]


@router.get("/classes/{class_id}/overview")
def class_overview(class_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    from app.services.membership import roles_in

    members = class_service.members(db, scope, class_id)
    roles = roles_in(db, scope.org_id, [u.id for u in members])
    out = []
    for u in members:
        if roles.get(u.id) != "student":
            continue
        latest = db.execute(
            select(Assignment, Attempt.status).join(Exam, Exam.id == Assignment.exam_id)
            .join(AssignmentTarget, AssignmentTarget.assignment_id == Assignment.id)
            .outerjoin(Attempt, (Attempt.assignment_id == Assignment.id) & (Attempt.student_id == u.id))
            .where(AssignmentTarget.user_id == u.id, Exam.source == "adaptive").order_by(Assignment.created_at.desc()).limit(1)).first()
        out.append({"student_id": u.id, "full_name": u.full_name, "username": u.username,
                    "weakest": [{"name": r["name"], "mastery": r["mastery"], "answers": r["answers"]} for r in weakest(mastery.rows_for(db, scope.org_id, u.id))],
                    "review": {"assignment_id": latest[0].id, "title": latest[0].title, "status": latest[1] or "not_started"} if latest else None})
    return out


class PracticeIn(BaseModel):
    count: int = 20
    subject_id: uuid.UUID | None = None


class ClassAdaptiveIn(BaseModel):
    count: int = 15
    open_at: datetime
    close_at: datetime
    duration_minutes: int = 30
    title: str | None = None


@router.post("/me/practice")
def start_practice(body: PracticeIn, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    att, exam, plan = adaptive.start_practice(db, scope, body.count, body.subject_id)
    return {"attempt_id": att.id, "question_count": len(plan.picks), **adaptive.plan_summary(exam)}


@router.get("/me/practice")
def my_practice(scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    if scope.role != "student":
        raise forbidden()
    rows = db.execute(select(Attempt, Exam).join(Exam, Exam.id == Attempt.exam_id)
                      .where(Attempt.student_id == scope.user.id, Attempt.assignment_id.is_(None)).order_by(Attempt.started_at.desc()).limit(20)).all()
    return [{"attempt_id": a.id, "title": e.title, "status": a.status, "started_at": a.started_at, "submitted_at": a.submitted_at,
             "score10": scaled(a.score or 0, a.max_score or 0) if a.status == "submitted" else None, **adaptive.plan_summary(e)} for a, e in rows]


@router.post("/classes/{class_id}/adaptive-assignments")
def class_adaptive(class_id: uuid.UUID, body: ClassAdaptiveIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    n = adaptive.assign_to_class(db, scope, class_id, body.count, body.open_at, body.close_at, body.duration_minutes, body.title)
    return {"created": n}
