from dataclasses import dataclass
import uuid

from app.modules.academic.application.common import load_year, require_admin, set_status
from app.modules.academic.application.dto import YearView, year_view
from app.modules.academic.domain.ports import SchoolYearRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class ChangeYearStatus:
    year_id: uuid.UUID
    status: str  # active (activate) | closed (close) | planning (reopen)


class ChangeYearStatusHandler:
    def __init__(self, years: SchoolYearRepository, audit: AuditTrail, uow: UnitOfWork):
        self.years, self.audit, self.uow = years, audit, uow

    def __call__(self, actor: Actor, cmd: ChangeYearStatus) -> YearView:
        require_admin(actor)
        y = set_status(self.years, self.audit, actor, load_year(self.years, actor.org_id, cmd.year_id), cmd.status)
        self.uow.commit()
        return year_view(y)
