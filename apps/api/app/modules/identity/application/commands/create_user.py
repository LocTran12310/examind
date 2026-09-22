from dataclasses import dataclass

from app.modules.identity.application.common import generate_username, home_code
from app.modules.identity.application.dto import CreatedUser, user_view
from app.modules.identity.domain.entities import User
from app.modules.identity.domain.ports import OrganizationRepository, PasswordHasher, Secrets, UserRepository
from app.modules.identity.domain.services.accounts import can_manage, check_new_password, check_role, check_username
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict, Forbidden, Invalid


@dataclass(frozen=True)
class CreateUser:
    full_name: str
    role: str = "student"
    username: str | None = None  # generated from the full name when empty
    email: str | None = None
    password: str | None = None  # a temporary one is generated when empty (must be changed on first login)


class CreateUserHandler:
    def __init__(self, users: UserRepository, orgs: OrganizationRepository, hasher: PasswordHasher, secrets: Secrets, audit: AuditTrail,
                 uow: UnitOfWork):
        self.users, self.orgs, self.hasher, self.secrets, self.audit, self.uow = users, orgs, hasher, secrets, audit, uow

    def __call__(self, actor: Actor, cmd: CreateUser) -> CreatedUser:
        check_role(cmd.role)
        if not can_manage(actor.role, cmd.role):
            raise Forbidden()
        if not (cmd.full_name or "").strip():
            raise Invalid("Họ tên không được để trống", "full_name")
        username = check_username(cmd.username) if cmd.username else generate_username(self.users, actor.org_id, cmd.full_name)
        if self.users.by_username(actor.org_id, username) is not None:
            raise Conflict("Tên đăng nhập đã tồn tại", "username")
        temp = None
        password = cmd.password
        if password:
            check_new_password(password)
        else:
            temp = password = self.secrets.temp_password()
        user = User(organization_id=actor.org_id, username=username, full_name=cmd.full_name.strip(), email=cmd.email or None,
                    role=cmd.role, password_hash=self.hasher.hash(password), must_change_password=temp is not None)
        self.users.add(user)
        self.audit.record(actor, actor.org_id, "user.create", "user", user.id, username=username, role=cmd.role)
        view = user_view(user, home_code(self.orgs, user))
        self.uow.commit()
        return CreatedUser(user=view, temp_password=temp)
