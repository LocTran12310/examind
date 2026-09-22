from dataclasses import dataclass
import uuid

from app.modules.identity.application.commands import _memberships
from app.modules.identity.application.common import load_org
from app.modules.identity.application.dto import MembershipView
from app.modules.identity.domain.ports import MembershipRepository, OrganizationRepository, UserRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class UpdateMembership:
    org_id: uuid.UUID
    user_id: uuid.UUID
    role: str | None = None
    is_active: bool | None = None
    side: str = "org"  # the admin screen it comes from: "org" (org → users) or "user" (user → orgs)


class UpdateMembershipHandler:
    def __init__(self, users: UserRepository, orgs: OrganizationRepository, members: MembershipRepository, audit: AuditTrail, uow: UnitOfWork):
        self.users, self.orgs, self.members, self.audit, self.uow = users, orgs, members, audit, uow

    def __call__(self, actor: Actor, cmd: UpdateMembership) -> MembershipView:
        _memberships.load_side(self.users, self.orgs, cmd.org_id, cmd.user_id, cmd.side)
        user, m = _memberships.update(self.users, self.members, self.audit, actor, cmd.org_id, cmd.user_id, cmd.role, cmd.is_active)
        view = _memberships.membership_view(self.orgs, m, user, load_org(self.orgs, cmd.org_id))
        self.uow.commit()
        return view
