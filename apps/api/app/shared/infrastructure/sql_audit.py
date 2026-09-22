"""AuditTrail over the audit_logs table (the shared port every module writes its history through)."""
import uuid

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.shared.application.actor import Actor
from app.shared.infrastructure.schema.audit import audit_logs


class SqlAuditTrail:
    def __init__(self, session: Session):
        self.session = session

    def record(self, actor: Actor | None, org_id: uuid.UUID, action: str, target_type: str, target_id: uuid.UUID | None = None, **data) -> None:
        self.session.execute(insert(audit_logs).values(
            id=uuid.uuid4(), organization_id=org_id, actor_id=actor.user_id if actor else None,
            action=action, target_type=target_type, target_id=target_id, data=data))
