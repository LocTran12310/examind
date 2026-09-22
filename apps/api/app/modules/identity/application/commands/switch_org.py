from dataclasses import dataclass
import uuid

from app.modules.identity.application.common import SessionIssuer, load_user, role_in
from app.modules.identity.application.dto import SessionView
from app.modules.identity.domain import errors
from app.modules.identity.domain.ports import MembershipRepository, OrganizationRepository, UserRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Forbidden


@dataclass(frozen=True)
class SwitchOrg:
    org_id: uuid.UUID
    refresh_token: str | None = None


class SwitchOrgHandler:
    """Opens another org of the user; the old refresh token must not reopen the previous org, so it is rotated."""

    def __init__(self, users: UserRepository, orgs: OrganizationRepository, members: MembershipRepository, issuer: SessionIssuer,
                 audit: AuditTrail, uow: UnitOfWork):
        self.users, self.orgs, self.members, self.issuer, self.audit, self.uow = users, orgs, members, issuer, audit, uow

    def __call__(self, actor: Actor, cmd: SwitchOrg) -> SessionView:
        user = load_user(self.users, actor.user_id)
        org = self.orgs.get(cmd.org_id)
        role = role_in(self.orgs, self.members, user, cmd.org_id) if org is not None else None
        if org is None or role is None:
            raise Forbidden()
        if not org.can_login:
            raise errors.org_suspended()
        user.last_org_id = org.id
        self.audit.record(actor, org.id, "org.switch", "organization", org.id)
        self.issuer.end(cmd.refresh_token)
        session = self.issuer.issue(user, org, role)
        self.uow.commit()
        return session
