from dataclasses import dataclass

from app.modules.identity.application.dto import OrgCreated, org_view
from app.modules.identity.application.ports import OrgSeeder
from app.modules.identity.domain.entities import Organization, User
from app.modules.identity.domain.ports import OrganizationRepository, PasswordHasher, Secrets, UserRepository
from app.modules.identity.domain.services.accounts import USERNAME_MSG, USERNAME_RE, check_org_code
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict, Invalid


@dataclass(frozen=True)
class CreateOrg:
    code: str
    name: str
    admin_username: str = "admin"
    admin_full_name: str = "Quản trị trung tâm"


class CreateOrgHandler:
    """A new org with its reference data, demo content and a first admin holding a temporary password (US-04, A-01)."""

    def __init__(self, orgs: OrganizationRepository, users: UserRepository, seeder: OrgSeeder, hasher: PasswordHasher, secrets: Secrets,
                 audit: AuditTrail, uow: UnitOfWork):
        self.orgs, self.users, self.seeder, self.hasher, self.secrets, self.audit, self.uow = orgs, users, seeder, hasher, secrets, audit, uow

    def __call__(self, actor: Actor, cmd: CreateOrg) -> OrgCreated:
        code = check_org_code(cmd.code)
        username = (cmd.admin_username or "").strip().lower()
        if not USERNAME_RE.match(username):
            raise Invalid(USERNAME_MSG, "admin_username")
        if self.orgs.code_taken(code):
            raise Conflict("Mã tổ chức đã tồn tại", "code")
        org = Organization(code=code, name=cmd.name.strip())
        self.orgs.add(org)
        password = self.secrets.temp_password()
        admin = User(organization_id=org.id, username=username, full_name=cmd.admin_full_name.strip(), role="org_admin",
                     password_hash=self.hasher.hash(password), must_change_password=True)
        self.seeder.seed_reference(org.id)
        self.users.add(admin)
        self.seeder.seed_demo(org.id)
        self.audit.record(actor, org.id, "org.create", "organization", org.id, code=code)
        view = org_view(org, 1)
        self.uow.commit()
        return OrgCreated(org=view, admin_username=admin.username, temp_password=password)
