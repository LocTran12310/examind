from dataclasses import dataclass

from app.modules.identity.application.common import SessionIssuer
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class Logout:
    refresh_token: str | None


class LogoutHandler:
    def __init__(self, issuer: SessionIssuer, uow: UnitOfWork):
        self.issuer, self.uow = issuer, uow

    def __call__(self, cmd: Logout) -> None:
        self.issuer.end(cmd.refresh_token)
        self.uow.commit()
