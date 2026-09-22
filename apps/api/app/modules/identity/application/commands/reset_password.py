from dataclasses import dataclass
import uuid

from app.modules.identity.application.common import Clock, load_member
from app.modules.identity.application.dto import Credential
from app.modules.identity.domain.ports import MembershipRepository, PasswordHasher, RefreshTokenRepository, Secrets, UserRepository
from app.modules.identity.domain.services.accounts import can_manage
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import Forbidden


@dataclass(frozen=True)
class ResetPassword:
    user_id: uuid.UUID


class ResetPasswordHandler:
    """A new temporary password; every session of the account ends and the lock is lifted."""

    def __init__(self, users: UserRepository, members: MembershipRepository, tokens: RefreshTokenRepository, hasher: PasswordHasher,
                 secrets: Secrets, audit: AuditTrail, uow: UnitOfWork, clock: Clock = utcnow):
        self.users, self.members, self.tokens, self.hasher, self.secrets = users, members, tokens, hasher, secrets
        self.audit, self.uow, self.clock = audit, uow, clock

    def __call__(self, actor: Actor, cmd: ResetPassword) -> Credential:
        user, m = load_member(self.users, self.members, actor.org_id, cmd.user_id)
        if not can_manage(actor.role, m.role):
            raise Forbidden()
        if user.organization_id != actor.org_id:
            raise Forbidden("Chỉ tổ chức gốc của tài khoản đặt lại được mật khẩu")
        password = self.secrets.temp_password()
        user.password_hash = self.hasher.hash(password)
        user.must_change_password = True
        user.failed_logins = 0
        user.locked_until = None
        self.tokens.revoke_user(user.id, self.clock())
        self.audit.record(actor, actor.org_id, "user.reset_password", "user", user.id)
        self.uow.commit()
        return Credential(user_id=user.id, username=user.username, full_name=user.full_name, temp_password=password)
