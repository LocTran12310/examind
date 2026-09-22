from dataclasses import dataclass
import uuid

from app.modules.identity.application.common import Clock, home_code, load_member
from app.modules.identity.application.dto import UserView, user_view
from app.modules.identity.application.ports import UserReader
from app.modules.identity.domain.entities import ORG_ROLES
from app.modules.identity.domain.ports import MembershipRepository, OrganizationRepository, RefreshTokenRepository, UserRepository
from app.modules.identity.domain.services.accounts import can_manage
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import Forbidden, Invalid


@dataclass(frozen=True)
class UpdateUser:
    user_id: uuid.UUID
    full_name: str | None = None
    email: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UpdateUserHandler:
    """Account fields belong to the home org; outside it only the role and the access to this org change (A-06, A-10)."""

    def __init__(self, users: UserRepository, members: MembershipRepository, orgs: OrganizationRepository, tokens: RefreshTokenRepository,
                 reader: UserReader, audit: AuditTrail, uow: UnitOfWork, clock: Clock = utcnow):
        self.users, self.members, self.orgs, self.tokens, self.reader = users, members, orgs, tokens, reader
        self.audit, self.uow, self.clock = audit, uow, clock

    def __call__(self, actor: Actor, cmd: UpdateUser) -> UserView:
        user, m = load_member(self.users, self.members, actor.org_id, cmd.user_id)
        home = user.organization_id == actor.org_id
        if not can_manage(actor.role, m.role):
            raise Forbidden()
        if cmd.role and cmd.role != m.role:
            if actor.role != "org_admin" or cmd.role not in ORG_ROLES:
                raise Forbidden()
            if home:
                user.role = cmd.role  # the home membership follows (A-06)
            m.role = cmd.role
        if not home and (cmd.full_name is not None or cmd.email is not None):
            raise Forbidden("Thông tin tài khoản do tổ chức gốc quản lý")
        if cmd.full_name is not None:
            if not cmd.full_name.strip():
                raise Invalid("Họ tên không được để trống", "full_name")
            user.full_name = cmd.full_name.strip()
        if cmd.email is not None:
            user.email = cmd.email or None
        if cmd.is_active is not None:
            if user.id == actor.user_id and not cmd.is_active:
                raise Forbidden("Không thể tự khóa tài khoản của mình")
            if home and cmd.is_active != user.is_active:
                user.is_active = cmd.is_active
                if not user.is_active:
                    self.tokens.revoke_user(user.id, self.clock())
            m.is_active = cmd.is_active  # outside the home org this only locks access to this org
        changed = {"full_name": cmd.full_name, "email": cmd.email, "role": cmd.role, "is_active": cmd.is_active}
        self.audit.record(actor, actor.org_id, "user.update", "user", user.id, fields=sorted(k for k, v in changed.items() if v is not None))
        self.uow.flush()
        view = user_view(user, home_code(self.orgs, user), m, self.reader.class_ids(actor.org_id, [user.id]).get(user.id))
        self.uow.commit()
        return view
