from dataclasses import dataclass
import uuid

from app.modules.audit.application.dto import AuditRow
from app.modules.audit.application.ports import AuditReader
from app.modules.audit.domain.services.history import check_reader, reads_every_org
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchAudit:
    request: SearchRequest
    related: uuid.UUID | None = None
    target_id: uuid.UUID | None = None
    organization_id: uuid.UUID | None = None


class SearchAuditHandler:
    """History = the audit log: org admins see their org, the platform admin every org."""

    def __init__(self, reader: AuditReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchAudit) -> Page[AuditRow]:
        check_reader(actor.role, actor.is_super)
        org_id = None if reads_every_org(actor.role, actor.is_super) else actor.org_id
        return self.reader.search(org_id, query.request, query.related, query.target_id, query.organization_id)
