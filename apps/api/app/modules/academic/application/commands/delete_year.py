from dataclasses import dataclass
import uuid

from app.modules.academic.application.common import load_year, require_admin
from app.modules.academic.domain.ports import SchoolYearRepository
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Conflict


@dataclass(frozen=True)
class DeleteYear:
    year_id: uuid.UUID


class DeleteYearHandler:
    """Only a year without classes that is not the active one."""

    def __init__(self, years: SchoolYearRepository, audit: AuditTrail, uow: UnitOfWork):
        self.years, self.audit, self.uow = years, audit, uow

    def __call__(self, actor: Actor, cmd: DeleteYear) -> None:
        require_admin(actor)
        y = load_year(self.years, actor.org_id, cmd.year_id)
        n = self.years.class_count(y.id)
        if n:
            raise Conflict(f"Năm học còn {n} lớp", code="in_use")
        if y.status == "active":
            raise Conflict("Không xóa được năm học đang học", code="in_use")
        self.years.remove(y)
        self.audit.record(actor, actor.org_id, "year.delete", "school_year", y.id, code=y.code)
        self.uow.commit()
