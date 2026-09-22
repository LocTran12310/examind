import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.taxonomy.application.dto import TagView
from app.shared.application.search import Page, SearchRequest
from app.shared.domain.errors import Invalid
from app.shared.infrastructure.schema.taxonomy import tags
from app.shared.infrastructure.sql_search import Col, search

TAG_COLS = {"group": Col(tags.c.group, "exact"), "name": Col(tags.c.name), "subject_id": Col(tags.c.subject_id, "uuid", sortable=False)}


class SqlTagReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID, req: SearchRequest, subject: str | None, include_shared: bool) -> Page[TagView]:
        stmt = select(tags.c.id, tags.c.group, tags.c.name, tags.c.subject_id).where(tags.c.organization_id == org_id)
        if subject == "shared":
            stmt = stmt.where(tags.c.subject_id.is_(None))
        elif subject:
            try:
                sid = uuid.UUID(subject)
            except ValueError:
                raise Invalid("Môn học không hợp lệ", "subject_id")
            stmt = stmt.where(or_(tags.c.subject_id == sid, tags.c.subject_id.is_(None)) if include_shared else tags.c.subject_id == sid)
        rows, total = search(self.session, stmt, req, TAG_COLS, text=[tags.c.name],
                             default_sort=[tags.c.group, func.lower(tags.c.name), tags.c.id], scalars=False)
        return Page([TagView(id=r.id, group=r.group, name=r.name, subject_id=r.subject_id) for r in rows], total, req.page, req.limit)
