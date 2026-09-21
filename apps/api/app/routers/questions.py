import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import not_found
from app.deps import OrgScope, org_scope
from app.models import Question
from app.schemas.questions import QuestionOut, QuestionPatch, question_out

router = APIRouter(prefix="/questions", tags=["questions"])


def _get(db: Session, scope: OrgScope, qid) -> Question:
    q = db.get(Question, qid)
    if q is None or q.organization_id != scope.org_id:
        raise not_found("Không tìm thấy câu hỏi")
    return q


@router.get("/demo", response_model=QuestionOut)
def demo(scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    q = db.scalar(select(Question).where(Question.organization_id == scope.org_id, Question.source == "demo").limit(1))
    if q is None:
        raise not_found("Chưa có câu hỏi mẫu")
    return question_out(q)


@router.get("/{question_id}")
def get_question(question_id: uuid.UUID, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    q = _get(db, scope, question_id)
    if scope.role == "student":
        # students never receive answers/solutions from this endpoint; exams expose them after submission
        return question_out(q, hide_answer=True)
    from app.routers.documents import parsed_many

    return parsed_many(db, [q])[0]


@router.patch("/{question_id}")
def patch_question(question_id: uuid.UUID, body: QuestionPatch, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    from app.core.errors import forbidden
    from app.routers.documents import parsed_many
    from app.services import review

    if scope.role not in ("org_admin", "teacher"):
        raise forbidden()
    q = review.edit(db, scope, question_id, body.model_dump(exclude_unset=True))
    return parsed_many(db, [q])[0]
