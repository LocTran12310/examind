"""Review workflow over questions.status (question-review ADR-03)."""
import uuid

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.core.errors import forbidden, not_found, validation
from app.deps import OrgScope
from app.models import Question, SourceDocument, User

STATUS_KEYS = ("auto_approved", "needs_review", "approved", "rejected", "duplicate")


def document_counts(db: Session, scope: OrgScope, mine: bool = False, doc_id=None) -> list[dict]:
    cols = [func.count(case((Question.status == s, 1))).label(s) for s in STATUS_KEYS]
    spot = func.count(case((and_(Question.spot_check.is_(True), Question.status == "auto_approved"), 1))).label("spot_pending")
    stmt = (select(SourceDocument, func.count(Question.id).label("total"), *cols, spot)
            .outerjoin(Question, Question.source_document_id == SourceDocument.id)
            .where(SourceDocument.organization_id == scope.org_id, SourceDocument.status == "parsed")
            .group_by(SourceDocument.id).order_by(SourceDocument.created_at.desc()))
    if mine:
        stmt = stmt.where(SourceDocument.assigned_to == scope.user.id)
    if doc_id:
        stmt = stmt.where(SourceDocument.id == doc_id)
    users = {}
    out = []
    for row in db.execute(stmt):
        doc = row[0]
        counts = {s: getattr(row, s) for s in STATUS_KEYS}
        done = counts["approved"] + counts["rejected"] + counts["duplicate"] + counts["auto_approved"] - row.spot_pending
        if doc.assigned_to and doc.assigned_to not in users:
            u = db.get(User, doc.assigned_to)
            users[doc.assigned_to] = u.full_name if u else None
        out.append({"document": doc, "total": row.total, "counts": counts, "spot_pending": row.spot_pending,
                    "progress": round(done / row.total, 2) if row.total else 1.0,
                    "assigned_to": doc.assigned_to, "assigned_name": users.get(doc.assigned_to)})
    return out


def assign(db: Session, scope: OrgScope, doc_id, user_id) -> SourceDocument:
    if scope.role != "org_admin":
        raise forbidden()
    doc = db.get(SourceDocument, doc_id)
    if doc is None or doc.organization_id != scope.org_id:
        raise not_found("Không tìm thấy tài liệu")
    if user_id is not None:
        u = db.get(User, uuid.UUID(str(user_id)))
        if u is None or u.organization_id != scope.org_id or u.role not in ("teacher", "org_admin"):
            raise validation("Chỉ giao cho giáo viên của trung tâm", "assigned_to")
    doc.assigned_to = uuid.UUID(str(user_id)) if user_id else None
    return doc
