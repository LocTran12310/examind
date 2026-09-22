"""Roster over the academic context's (classes) and the identity context's (memberships) application APIs, handed in
by the composition root; the people's names are read from the identity tables. Analytics never imports another module."""
from typing import Protocol
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.analytics.domain.value_objects import Member
from app.shared.application.actor import Actor
from app.shared.infrastructure.schema.identity import users


class _AcademicApi(Protocol):
    def member_ids(self, actor: Actor, class_id: uuid.UUID) -> list[uuid.UUID]: ...


class _IdentityApi(Protocol):
    def roles_in(self, org_id: uuid.UUID, user_ids) -> dict[uuid.UUID, str]: ...

    def member_ids(self, org_id: uuid.UUID, user_ids, role: str | tuple[str, ...] | None = None) -> set[uuid.UUID]: ...


class AcademicRoster:
    def __init__(self, session: Session, academic: _AcademicApi, identity: _IdentityApi):
        self.session, self.academic, self.identity = session, academic, identity

    def _people(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple]:
        if not ids:
            return {}
        rows = self.session.execute(select(users.c.id, users.c.full_name, users.c.username, users.c.is_active).where(users.c.id.in_(ids)))
        return {r.id: r for r in rows}

    def class_members(self, actor: Actor, class_id: uuid.UUID) -> list[Member]:
        ids = self.academic.member_ids(actor, class_id)
        people = self._people(list(ids))
        roles = self.identity.roles_in(actor.org_id, list(ids))
        return [Member(i, people[i].full_name, people[i].username, people[i].is_active, roles.get(i)) for i in ids if i in people]

    def is_member(self, org_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return bool(self.identity.member_ids(org_id, {user_id}))

    def person(self, user_id: uuid.UUID) -> Member | None:
        r = self._people([user_id]).get(user_id)
        return Member(r.id, r.full_name, r.username, r.is_active) if r else None
