from datetime import datetime
import uuid

from pydantic import BaseModel


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
