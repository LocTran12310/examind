from dataclasses import dataclass

from app.modules.identity.application.common import Clock, SessionIssuer
from app.modules.identity.application.dto import SessionView
from app.modules.identity.domain import errors
from app.modules.identity.domain.ports import OrganizationRepository, RefreshTokenRepository, Secrets, UserRepository
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow


@dataclass(frozen=True)
class RefreshSession:
    refresh_token: str


class RefreshSessionHandler:
    """Rotates the refresh token; a revoked token coming back means it leaked, so every session of the user ends."""

    def __init__(self, tokens: RefreshTokenRepository, users: UserRepository, orgs: OrganizationRepository, secrets: Secrets,
                 issuer: SessionIssuer, uow: UnitOfWork, clock: Clock = utcnow):
        self.tokens, self.users, self.orgs, self.secrets, self.issuer, self.uow, self.clock = tokens, users, orgs, secrets, issuer, uow, clock

    def __call__(self, cmd: RefreshSession) -> SessionView:
        if not cmd.refresh_token:
            raise errors.session_expired()
        token = self.tokens.by_hash(self.secrets.digest(cmd.refresh_token))
        if token is None:
            raise errors.session_expired()
        now = self.clock()
        if token.revoked_at is not None:
            self.tokens.revoke_user(token.user_id, now)
            self.uow.commit()
            raise errors.session_expired()
        if token.expires_at <= now:
            raise errors.session_expired()
        user = self.users.get(token.user_id)
        home = self.orgs.get(user.organization_id) if user is not None else None
        if user is None or not user.is_active or home is None or not home.can_login:
            token.revoked_at = now
            self.uow.commit()
            raise errors.session_expired()
        token.revoked_at = now
        session = self.issuer.issue(user)
        self.uow.commit()
        return session
