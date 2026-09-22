from dataclasses import dataclass
from datetime import date
import uuid

from app.modules.academic.application.common import audit_year, load_year, require_admin
from app.modules.academic.application.dto import YearView, year_view
from app.modules.academic.domain.ports import SchoolYearRepository
from app.modules.academic.domain.services import calendar
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class UpdateYear:
    year_id: uuid.UUID
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    terms: list[dict] | None = None


class UpdateYearHandler:
    """A closed year stays editable; the change is in the history with the closed-year flag."""

    def __init__(self, years: SchoolYearRepository, audit: AuditTrail, uow: UnitOfWork):
        self.years, self.audit, self.uow = years, audit, uow

    def __call__(self, actor: Actor, cmd: UpdateYear) -> YearView:
        require_admin(actor)
        y = load_year(self.years, actor.org_id, cmd.year_id)
        before = {"name": y.name, "start_date": str(y.start_date), "end_date": str(y.end_date)}
        if cmd.name:
            y.name = cmd.name.strip()
        y.start_date, y.end_date = cmd.start_date or y.start_date, cmd.end_date or y.end_date
        calendar.check_bounds(y)
        calendar.apply_terms(y, cmd.terms)
        after = {"name": y.name, "start_date": str(y.start_date), "end_date": str(y.end_date)}
        audit_year(self.audit, actor, y, "year.update", changes={k: [before[k], after[k]] for k in after if before[k] != after[k]},
                   terms=bool(cmd.terms))
        self.uow.commit()
        return year_view(y)
