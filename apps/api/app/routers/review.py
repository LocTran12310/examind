import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import not_found
from app.deps import OrgScope
from app.deps import staff_scope
from app.schemas.documents import document_out
from app.routers.documents import parsed_many
from app.schemas.documents import ParsedQuestionOut
from app.schemas.questions import ActionIn
from app.schemas.review import AssignIn, ReviewDocumentOut
from app.schemas.common import Page
from app.services import review
from app.services.paging import ListParams, list_params

router = APIRouter(prefix="/review", tags=["review"])


def _out(row) -> ReviewDocumentOut:
    return ReviewDocumentOut(**{**row, "document": document_out(row["document"])})


@router.get("/documents", response_model=Page[ReviewDocumentOut])
def review_documents(mine: bool = False, params: ListParams = Depends(list_params), scope: OrgScope = Depends(staff_scope),
                     db: Session = Depends(get_db)):
    """Column filters: filename, source_name (text) · assigned_to · created_at (date); sort also by total, needs_review."""
    rows, total = review.list_review_documents(db, scope, params, mine)
    return Page(items=[_out(r) for r in rows], total=total, page=params.page, page_size=params.page_size)


@router.get("/documents/{doc_id}", response_model=ReviewDocumentOut)
def review_document(doc_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    rows = review.document_counts(db, scope, doc_id=doc_id)
    if not rows:
        raise not_found("Không tìm thấy tài liệu")
    return _out(rows[0])


@router.patch("/documents/{doc_id}", response_model=ReviewDocumentOut)
def assign(doc_id: uuid.UUID, body: AssignIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    review.assign(db, scope, doc_id, body.assigned_to)
    db.flush()
    return _out(review.document_counts(db, scope, doc_id=doc_id)[0])


@router.get("/documents/{doc_id}/queue", response_model=list[ParsedQuestionOut])
def review_queue(doc_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    qs = review.queue(db, scope, doc_id)
    return parsed_many(db, qs, {q.id: review.group_of(q) for q in qs})


@router.post("/questions/{qid}/action", response_model=ParsedQuestionOut)
def question_action(qid: uuid.UUID, body: ActionIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    q = review.act(db, scope, qid, body.action)
    return parsed_many(db, [q])[0]


class AnswerKeyIn(BaseModel):
    text: str


@router.post("/documents/{doc_id}/answer-key")
def answer_key(doc_id: uuid.UUID, body: AnswerKeyIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return review.apply_answer_key(db, scope, doc_id, body.text)


@router.post("/documents/{doc_id}/approve-confident")
def approve_confident(doc_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return {"approved": review.approve_confident(db, scope, doc_id)}


@router.post("/key-audit")
def key_audit(scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    from app.services import key_audit as audit_service

    return {"flagged": [str(i) for i in audit_service.audit(db, scope.org_id)]}


@router.get("/flagged", response_model=Page[ParsedQuestionOut])
def flagged(params: ListParams = Depends(list_params), scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    qs, total = review.flagged_questions(db, scope, params)
    return Page(items=parsed_many(db, qs, {q.id: "Nghi sai đáp án" for q in qs}), total=total, page=params.page, page_size=params.page_size)
