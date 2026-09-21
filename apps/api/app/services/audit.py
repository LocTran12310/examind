from sqlalchemy.orm import Session

from app.models import AuditLog, User


def record(db: Session, actor: User | None, org_id, action: str, target_type: str, target_id=None, **data) -> None:
    db.add(AuditLog(
        organization_id=org_id,
        actor_id=actor.id if actor else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        data=data,
    ))
