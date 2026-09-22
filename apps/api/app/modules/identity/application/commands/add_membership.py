from dataclasses import dataclass
import uuid

from app.modules.identity.application.commands import _memberships
from app.modules.identity.application.common import find_account, load_account, load_org
from app.modules.identity.application.dto import MembershipView
from app.modules.identity.domain.ports import MembershipRepository, OrganizationRepository, UserRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class AddMembership:
    """From the org side (`org_code` + `username` name the account) or from the user side (`user_id`)."""
    org_id: uuid.UUID
    role: str = "teacher"
    user_id: uuid.UUID | None = None
    org_code: str | None = None
    username: str | None = None


class AddMembershipHandler:
    def __init__(self, users: UserRepository, orgs: OrganizationRepository, members: MembershipRepository, audit: AuditTrail, uow: UnitOfWork):
        self.users, self.orgs, self.members, self.audit, self.uow = users, orgs, members, audit, uow

    def __call__(self, actor: Actor, cmd: AddMembership) -> MembershipView:
        if cmd.user_id is not None:
            user = load_account(self.users, cmd.user_id)
        else:
            load_org(self.orgs, cmd.org_id)
            user = find_account(self.orgs, self.users, cmd.org_code or "", cmd.username or "")
        m = _memberships.add(self.orgs, self.members, self.audit, actor, cmd.org_id, user, cmd.role)
        view = _memberships.membership_view(self.orgs, m, user, load_org(self.orgs, cmd.org_id))
        self.uow.commit()
        return view
