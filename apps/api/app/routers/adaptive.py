import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import forbidden, not_found
from app.deps import OrgScope, org_scope
from app.models import Assignment, AssignmentTarget, Attempt, Exam, User
from app.routers.users import staff_scope
from app.services import classes as class_service, mastery

router = APIRouter(tags=["adaptive"])


@router.get("/me/mastery")
def my_mastery(scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    if scope.role != "student":
        raise forbidden()
    return mastery.rows_for(db, scope.org_id, scope.user.id)


@router.get("/students/{student_id}/mastery")
def student_mastery(student_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    u = db.get(User, student_id)
    if u is None or u.organization_id != scope.org_id:
        raise not_found("Không tìm thấy học sinh")
    return mastery.rows_for(db, scope.org_id, student_id)


def weakest(rows: list[dict], n: int = 3) -> list[dict]:
    tracked = [r for r in rows if r["tracked"] and r["mastery"] is not None]
    return sorted(tracked, key=lambda r: r["mastery"])[:n]


@router.get("/classes/{class_id}/overview")
def class_overview(class_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    members = class_service.members(db, scope, class_id)
    out = []
    for u in members:
        if u.role != "student":
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
