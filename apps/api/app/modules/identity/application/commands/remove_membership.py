from dataclasses import dataclass
import uuid

from app.modules.identity.application.commands import _memberships
from app.modules.identity.application.ports import ClassDirectory
from app.modules.identity.domain.ports import MembershipRepository, OrganizationRepository, UserRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class RemoveMembership:
    org_id: uuid.UUID
    user_id: uuid.UUID
    side: str = "org"  # "org" (org → users) or "user" (user → orgs)


class RemoveMembershipHandler:
    def __init__(self, users: UserRepository, orgs: OrganizationRepository, members: MembershipRepository, classes: ClassDirectory,
                 audit: AuditTrail, uow: UnitOfWork):
        self.users, self.orgs, self.members, self.classes, self.audit, self.uow = users, orgs, members, classes, audit, uow

    def __call__(self, actor: Actor, cmd: RemoveMembership) -> None:
        _memberships.load_side(self.users, self.orgs, cmd.org_id, cmd.user_id, cmd.side)
        _memberships.remove(self.users, self.members, self.classes, self.audit, actor, cmd.org_id, cmd.user_id)
        self.uow.commit()
