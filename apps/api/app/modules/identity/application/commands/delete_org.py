from dataclasses import dataclass
import uuid

from app.modules.identity.application.commands._orgs import guard_system
from app.modules.identity.application.common import Clock, load_org
from app.modules.identity.domain.ports import OrganizationRepository, RefreshTokenRepository, UserRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import Conflict


@dataclass(frozen=True)
class DeleteOrg:
    org_id: uuid.UUID
    hard: bool = False  # soft delete hides the org; a hard delete only for an org nobody but its admins uses


class DeleteOrgHandler:
    def __init__(self, orgs: OrganizationRepository, users: UserRepository, tokens: RefreshTokenRepository, audit: AuditTrail,
                 uow: UnitOfWork, clock: Clock = utcnow):
        self.orgs, self.users, self.tokens, self.audit, self.uow, self.clock = orgs, users, tokens, audit, uow, clock

    def __call__(self, actor: Actor, cmd: DeleteOrg) -> None:
        org = load_org(self.orgs, cmd.org_id)
        guard_system(org)
        if not cmd.hard:
            org.deleted_at = self.clock()
            self.tokens.revoke_org(org.id, self.clock())
            self.audit.record(actor, org.id, "org.delete", "organization", org.id)
        else:
            if self.users.non_admin_count(org.id):
                raise Conflict("Chỉ xóa vĩnh viễn được tổ chức chưa có người dùng", code="org_not_empty")
            self.orgs.purge(org)
        self.uow.commit()
