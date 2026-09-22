"""Users in several organisations (school-structure-multi-org ADR-02…ADR-04) — moved to app.modules.identity
(architecture-refactor). The read helpers the old layout still calls wrap the identity context's API."""
from sqlalchemy.orm import Session

from app.models import User
from app.modules.identity.domain.entities import ORG_ROLES  # noqa: F401
from app.modules.identity.interface.deps import identity_api


def is_super(user: User) -> bool:
    return user.role == "super_admin"


def role_in(db: Session, user: User, org_id) -> str | None:
    """The user's role in `org_id`, or None when they may not work there."""
    return identity_api(db).role_in(user.id, org_id)


def member_ids(db: Session, org_id, ids, role: str | tuple[str, ...] | None = None) -> set:
    return identity_api(db).member_ids(org_id, set(ids or ()), role) if ids else set()


def roles_in(db: Session, org_id, user_ids) -> dict:
    """{user_id: role} for active memberships of `org_id`."""
    return identity_api(db).roles_in(org_id, user_ids)
