"""The history list (SQLAlchemy Core over audit_logs; names and codes from the identity tables, ADR-01)."""
import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.audit.application.dto import AuditRow
from app.modules.audit.domain.entities import AuditEntry
from app.modules.audit.infrastructure import orm  # noqa: F401  (mapping)
from app.shared.application.search import Page, SearchRequest
from app.shared.infrastructure.schema.audit import audit_logs
from app.shared.infrastructure.schema.identity import organizations, users
from app.shared.infrastructure.sql_search import Col, search

a_c = audit_logs.c
COLS = {
    "action": Col(a_c.action),
    "target_type": Col(a_c.target_type, "exact"),
    "target_id": Col(a_c.target_id, "uuid"),
    "created_at": Col(a_c.created_at, "date"),
    "actor_id": Col(a_c.actor_id, "uuid"),
    "organization_id": Col(a_c.organization_id, "uuid"),
}


class SqlAuditReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID | None, req: SearchRequest, related: uuid.UUID | None = None,
               target_id: uuid.UUID | None = None, organization_id: uuid.UUID | None = None) -> Page[AuditRow]:
        stmt = (select(AuditEntry, users.c.full_name, organizations.c.code).outerjoin(users, users.c.id == a_c.actor_id)
                .join(organizations, organizations.c.id == a_c.organization_id))
        if org_id is not None:
            stmt = stmt.where(a_c.organization_id == org_id)
        if target_id:
            stmt = stmt.where(a_c.target_id == target_id)
        if organization_id:
            stmt = stmt.where(a_c.organization_id == organization_id)
        if related:
            stmt = stmt.where(or_(a_c.target_id == related, a_c.data["user_ids"].contains([str(related)])))
        rows, total = search(self.session, stmt, req, COLS, text=[a_c.action], default_sort=[a_c.created_at.desc(), a_c.id], scalars=False)
        return Page([AuditRow(e, name, code) for e, name, code in rows], total, req.page, req.limit)
