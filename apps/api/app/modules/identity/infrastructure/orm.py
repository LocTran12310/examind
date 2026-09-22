"""Maps the identity dataclasses onto their tables (architecture-refactor ADR-01). Importing this module is enough;
mapping happens once. `User.organization` (the home org) stays for the old layout's readers."""
from sqlalchemy import event, inspect
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import relationship

from app.modules.identity.domain.entities import Membership, Organization, RefreshToken, User
from app.shared.infrastructure.db import mapper_registry
from app.shared.infrastructure.schema.identity import organization_members, organizations, refresh_tokens, users


def _mapped(cls) -> bool:
    return any(m.class_ is cls for m in mapper_registry.mappers)


def _home_membership(mapper, connection, user: User) -> None:
    """Every account gets its home membership, whichever code path created it."""
    connection.execute(
        pg_insert(organization_members)
        .values(user_id=user.id, organization_id=user.organization_id, role=user.role, is_active=True)
        .on_conflict_do_nothing()
    )


def _sync_home_role(mapper, connection, user: User) -> None:
    """users.role mirrors the home membership (A-06)."""
    if inspect(user).attrs.role.history.has_changes():
        connection.execute(
            organization_members.update()
            .where(organization_members.c.user_id == user.id, organization_members.c.organization_id == user.organization_id)
            .values(role=user.role)
        )


if not _mapped(User):
    mapper_registry.map_imperatively(Organization, organizations)
    mapper_registry.map_imperatively(User, users, properties={
        "organization": relationship(Organization, lazy="joined", foreign_keys=[users.c.organization_id], viewonly=True),
    })
    mapper_registry.map_imperatively(Membership, organization_members)
    mapper_registry.map_imperatively(RefreshToken, refresh_tokens)
    event.listen(User, "after_insert", _home_membership)
    event.listen(User, "after_update", _sync_home_role)
