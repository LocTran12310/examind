from typing import Protocol
import uuid

from app.modules.audit.application.dto import AuditRow
from app.shared.application.search import Page, SearchRequest


class AuditReader(Protocol):
    def search(self, org_id: uuid.UUID | None, req: SearchRequest, related: uuid.UUID | None = None,
               target_id: uuid.UUID | None = None, organization_id: uuid.UUID | None = None) -> Page[AuditRow]:
        """Entries of the org (every org when None), newest first, with the actor's name and the org's code.
        `related` also matches entries whose data lists that user (class member changes of a student). Filters: action
        (text) · target_type (enum) · target_id, actor_id, organization_id (uuid) · created_at (date)."""
        ...
