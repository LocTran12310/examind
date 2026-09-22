from dataclasses import dataclass
from datetime import timedelta

from app.modules.identity.application.common import Clock, SessionIssuer
from app.modules.identity.application.dto import SessionView
from app.modules.identity.application.ports import AuthPolicy, LoginThrottle
from app.modules.identity.domain import errors
from app.modules.identity.domain.ports import OrganizationRepository, PasswordHasher, UserRepository
from app.modules.identity.domain.services.accounts import normalise_org_code
from app.modules.identity.domain.services.lockout import locked_minutes, record_failure, record_success
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow


@dataclass(frozen=True)
class Login:
    org_code: str
    username: str
    password: str
    client_ip: str = "?"


class LoginHandler:
    """Org code + username + password → a session. Every wrong input answers the same error (ADR-05)."""

    def __init__(self, orgs: OrganizationRepository, users: UserRepository, hasher: PasswordHasher, issuer: SessionIssuer,
                 throttle: LoginThrottle, policy: AuthPolicy, uow: UnitOfWork, clock: Clock = utcnow):
        self.orgs, self.users, self.hasher, self.issuer, self.throttle = orgs, users, hasher, issuer, throttle
        self.policy, self.uow, self.clock = policy, uow, clock

    def __call__(self, cmd: Login) -> SessionView:
        if not self.throttle.hit(cmd.client_ip):
            raise errors.too_many_logins()
        org = self.orgs.by_code(normalise_org_code(cmd.org_code))
        user = self.users.by_username(org.id, (cmd.username or "").strip()) if org is not None else None
        now = self.clock()
        minutes = locked_minutes(user, now) if user is not None else None
        if minutes is not None:
            raise errors.account_locked(minutes)
        ok = self.hasher.verify(cmd.password or "", user.password_hash if user else None)
        if not ok or user is None or not user.is_active:
            if user is not None:
                record_failure(user, now, timedelta(minutes=self.policy.login_lock_minutes), self.policy.login_max_failures)
                self.uow.commit()
            raise errors.invalid_credentials()
        if not org.can_login:
            raise errors.org_suspended()
        record_success(user, now)
        session = self.issuer.issue(user)
        self.uow.commit()
        return session
