"""AuditTrail over the audit_logs table (Core insert: the declarative AuditLog stays in the old layout)."""
import uuid

from sqlalchemy import column, insert, table
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Session

from app.shared.application.actor import Actor

_audit_logs = table(
    "audit_logs", column("id", UUID(as_uuid=True)), column("organization_id", UUID(as_uuid=True)), column("actor_id", UUID(as_uuid=True)),
    column("action"), column("target_type"), column("target_id", UUID(as_uuid=True)), column("data", JSONB),
)


class SqlAuditTrail:
    def __init__(self, session: Session):
        self.session = session

    def record(self, actor: Actor | None, org_id: uuid.UUID, action: str, target_type: str, target_id: uuid.UUID | None = None, **data) -> None:
        self.session.execute(insert(_audit_logs).values(
            id=uuid.uuid4(), organization_id=org_id, actor_id=actor.user_id if actor else None,
            action=action, target_type=target_type, target_id=target_id, data=data))
