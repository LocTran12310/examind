import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import OrgScope, org_scope
from app.routers.users import staff_scope
from app.schemas.assignments import (AssignmentIn, AssignmentOut, AssignmentPatch, MyAssignmentOut, assignment_out, attempt_brief)
from app.services import assignments

router = APIRouter(tags=["assignments"])


@router.get("/assignments", response_model=list[AssignmentOut])
def list_assignments(exam_id: uuid.UUID | None = None, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return [assignment_out(r["assignment"], students=r["students"], submitted=r["submitted"], classes=r["classes"])
            for r in assignments.list_for_staff(db, scope, exam_id)]


@router.post("/assignments", response_model=AssignmentOut, status_code=201)
def create_assignment(body: AssignmentIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    data = body.model_dump(exclude={"exam_id", "class_ids", "user_ids"})
    a = assignments.create(db, scope, body.exam_id, data, body.class_ids, body.user_ids)
    return assignment_out(a, students=len(assignments.student_ids(db, a)))


@router.get("/assignments/{aid}", response_model=AssignmentOut)
def get_assignment(aid: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    a = assignments.get(db, scope, aid)
    return assignment_out(a, students=len(assignments.student_ids(db, a)))


@router.patch("/assignments/{aid}", response_model=AssignmentOut)
def patch_assignment(aid: uuid.UUID, body: AssignmentPatch, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return assignment_out(assignments.update(db, scope, aid, body.model_dump(exclude_unset=True)))


@router.delete("/assignments/{aid}", status_code=204)
def delete_assignment(aid: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    assignments.delete(db, scope, aid)
    return Response(status_code=204)


@router.get("/me/assignments", response_model=list[MyAssignmentOut])
def my_assignments(scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    from app.services.attempts import results_visible

    out = []
    for r in assignments.me_assignments(db, scope):
        a = r["assignment"]
        out.append(MyAssignmentOut(assignment=assignment_out(a), state=r["state"], attempts_left=r["attempts_left"],
                                   attempts=[attempt_brief(t, show_score=results_visible(a, t, score_only=True)) for t in r["attempts"]]))
    return out


@router.post("/assignments/{aid}/start")
def start(aid: uuid.UUID, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    att = assignments.start(db, scope, aid)
    return {"attempt_id": att.id}
