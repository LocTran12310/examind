from dataclasses import dataclass
from datetime import date

from app.modules.academic.application.common import require_admin
from app.modules.academic.application.dto import YearView, year_view
from app.modules.academic.domain.ports import SchoolYearRepository
from app.modules.academic.domain.services import calendar
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict


@dataclass(frozen=True)
class CreateYear:
    code: str
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    terms: list[dict] | None = None  # [{code: hk1|hk2, start_date, end_date}]


class CreateYearHandler:
    def __init__(self, years: SchoolYearRepository, audit: AuditTrail, uow: UnitOfWork):
        self.years, self.audit, self.uow = years, audit, uow

    def __call__(self, actor: Actor, cmd: CreateYear) -> YearView:
        require_admin(actor)
        code = calendar.check_code(cmd.code)
        if self.years.by_code(actor.org_id, code) is not None:
            raise Conflict("Năm học đã tồn tại", "code")
        y = calendar.new_year(actor.org_id, code, cmd.name, cmd.start_date, cmd.end_date)
        calendar.apply_terms(y, cmd.terms)
        self.years.add(y)
        self.audit.record(actor, actor.org_id, "year.create", "school_year", y.id, code=code)
        self.uow.commit()
        return year_view(y)
