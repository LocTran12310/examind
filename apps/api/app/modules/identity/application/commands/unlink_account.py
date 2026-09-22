from dataclasses import dataclass
import uuid

from app.modules.identity.application.commands import _memberships
from app.modules.identity.application.common import require_org_admin
from app.modules.identity.application.ports import ClassDirectory
from app.modules.identity.domain.ports import MembershipRepository, UserRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class UnlinkAccount:
    user_id: uuid.UUID


class UnlinkAccountHandler:
    """Access to this org ends and its class memberships go; the account keeps working in its other orgs."""

    def __init__(self, users: UserRepository, members: MembershipRepository, classes: ClassDirectory, audit: AuditTrail, uow: UnitOfWork):
        self.users, self.members, self.classes, self.audit, self.uow = users, members, classes, audit, uow

    def __call__(self, actor: Actor, cmd: UnlinkAccount) -> None:
        require_org_admin(actor)
        _memberships.remove(self.users, self.members, self.classes, self.audit, actor, actor.org_id, cmd.user_id)
        self.uow.commit()
