from dataclasses import dataclass

from app.modules.identity.application.commands import _memberships
from app.modules.identity.application.common import find_account, home_code, require_org_admin
from app.modules.identity.application.dto import UserView, user_view
from app.modules.identity.domain.ports import MembershipRepository, OrganizationRepository, UserRepository
from app.modules.identity.domain.services.accounts import check_role
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class LinkAccount:
    org_code: str  # the account's home org
    username: str
    role: str = "teacher"


class LinkAccountHandler:
    """An org admin adds an existing account of another organisation (A-10)."""

    def __init__(self, users: UserRepository, orgs: OrganizationRepository, members: MembershipRepository, audit: AuditTrail, uow: UnitOfWork):
        self.users, self.orgs, self.members, self.audit, self.uow = users, orgs, members, audit, uow

    def __call__(self, actor: Actor, cmd: LinkAccount) -> UserView:
        require_org_admin(actor)
        check_role(cmd.role)
        user = find_account(self.orgs, self.users, cmd.org_code, cmd.username)
        m = _memberships.add(self.orgs, self.members, self.audit, actor, actor.org_id, user, cmd.role)
        view = user_view(user, home_code(self.orgs, user), m, [])
        self.uow.commit()
        return view
