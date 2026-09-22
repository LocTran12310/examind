from datetime import datetime
import uuid

from pydantic import BaseModel

from app.modules.audit.application.dto import AuditRow
from app.shared.interface.search_schemas import SearchBody


class AuditSearchBody(SearchBody):
    """Scope parameters of a history panel (one target, one org, or anything that mentions a user)."""
    related: uuid.UUID | None = None
    target_id: uuid.UUID | None = None
    organization_id: uuid.UUID | None = None


class AuditOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    organization_id: uuid.UUID
    organization_code: str | None
    actor_id: uuid.UUID | None
    actor_name: str | None
    action: str
    target_type: str
    target_id: uuid.UUID | None
    data: dict


def audit_out(r: AuditRow) -> AuditOut:
    e = r.entry
    return AuditOut(id=e.id, created_at=e.created_at, organization_id=e.organization_id, organization_code=r.organization_code,
                    actor_id=e.actor_id, actor_name=r.actor_name, action=e.action, target_type=e.target_type, target_id=e.target_id,
                    data=e.data or {})
