import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import not_found
from app.deps import OrgScope
from app.routers.users import staff_scope
from app.schemas.documents import document_out
from app.schemas.review import AssignIn, ReviewDocumentOut
from app.services import review

router = APIRouter(prefix="/review", tags=["review"])


def _out(row) -> ReviewDocumentOut:
    return ReviewDocumentOut(**{**row, "document": document_out(row["document"])})


@router.get("/documents", response_model=list[ReviewDocumentOut])
def review_documents(mine: bool = False, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return [_out(r) for r in review.document_counts(db, scope, mine)]


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
