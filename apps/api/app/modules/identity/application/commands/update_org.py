from dataclasses import dataclass
import uuid

from app.modules.identity.application.commands._orgs import guard_system
from app.modules.identity.application.common import load_org
from app.modules.identity.application.dto import OrgView, org_view
from app.modules.identity.application.ports import OrgReader
from app.modules.identity.domain.ports import OrganizationRepository
from app.modules.identity.domain.services.accounts import check_org_code
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict, Invalid


@dataclass(frozen=True)
class UpdateOrg:
    org_id: uuid.UUID
    code: str | None = None  # renaming the login code is audited; the system org keeps its code
    name: str | None = None


class UpdateOrgHandler:
    def __init__(self, orgs: OrganizationRepository, reader: OrgReader, audit: AuditTrail, uow: UnitOfWork):
        self.orgs, self.reader, self.audit, self.uow = orgs, reader, audit, uow

    def __call__(self, actor: Actor, cmd: UpdateOrg) -> OrgView:
        org = load_org(self.orgs, cmd.org_id)
        if cmd.code is not None and cmd.code.strip().lower() != org.code:
            guard_system(org)
            new = check_org_code(cmd.code)
            if self.orgs.code_taken(new, exclude_id=org.id):
                raise Conflict("Mã tổ chức đã tồn tại", "code")
            self.audit.record(actor, org.id, "org.rename_code", "organization", org.id, old=org.code, new=new)
            org.code = new
        if cmd.name is not None:
            if not cmd.name.strip():
                raise Invalid("Tên không được để trống", "name")
            org.name = cmd.name.strip()
        self.audit.record(actor, org.id, "org.update", "organization", org.id)
        self.uow.flush()
        view = org_view(org, self.reader.user_counts([org.id]).get(org.id, 0))
        self.uow.commit()
        return view
