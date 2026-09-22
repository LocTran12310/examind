from dataclasses import dataclass
import uuid

from app.modules.identity.application.commands._orgs import guard_system
from app.modules.identity.application.common import Clock, load_org
from app.modules.identity.application.dto import OrgView, org_view
from app.modules.identity.domain.ports import OrganizationRepository, RefreshTokenRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow


@dataclass(frozen=True)
class ChangeOrgStatus:
    org_id: uuid.UUID
    status: str  # active | suspended


class ChangeOrgStatusHandler:
    """Suspending an org ends the sessions of its accounts; they cannot log in until it is active again."""

    def __init__(self, orgs: OrganizationRepository, tokens: RefreshTokenRepository, audit: AuditTrail, uow: UnitOfWork, clock: Clock = utcnow):
        self.orgs, self.tokens, self.audit, self.uow, self.clock = orgs, tokens, audit, uow, clock

    def __call__(self, actor: Actor, cmd: ChangeOrgStatus) -> OrgView:
        org = load_org(self.orgs, cmd.org_id)
        guard_system(org)
        org.status = cmd.status
        if cmd.status == "suspended":
            self.tokens.revoke_org(org.id, self.clock())
        self.audit.record(actor, org.id, f"org.{cmd.status}", "organization", org.id)
        view = org_view(org)
        self.uow.commit()
        return view
