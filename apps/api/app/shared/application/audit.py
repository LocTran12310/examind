from typing import Protocol
import uuid

from app.shared.application.actor import Actor


class AuditTrail(Protocol):
    """Who changed what: one entry per business change, written in the command's transaction."""

    def record(self, actor: Actor | None, org_id: uuid.UUID, action: str, target_type: str, target_id: uuid.UUID | None = None, **data) -> None: ...
