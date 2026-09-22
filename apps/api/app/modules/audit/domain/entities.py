"""Audit context: the history of business changes (school-years ADR-05). Every module writes it through the shared
AuditTrail port; this context reads it back."""
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.shared.domain.ids import new_id


@dataclass(eq=False)
class AuditEntry:
    organization_id: uuid.UUID
    action: str
    target_type: str
    actor_id: uuid.UUID | None = None
    target_id: uuid.UUID | None = None
    data: dict = field(default_factory=dict)
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None
