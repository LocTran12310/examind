import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import OrgScope, org_scope
from app.services import record

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/{student_id}/record")
def student_record(student_id: uuid.UUID, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    """Hồ sơ học sinh: classes per year with enrollment status, results per year, term and top-level topic."""
    return record.record(db, scope, student_id)
