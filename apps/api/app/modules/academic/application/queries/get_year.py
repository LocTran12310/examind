from dataclasses import dataclass
import uuid

from app.modules.academic.application.common import load_year
from app.modules.academic.application.dto import YearView, year_view
from app.modules.academic.domain.ports import SchoolYearRepository
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class GetYear:
    year_id: uuid.UUID


class GetYearHandler:
    def __init__(self, years: SchoolYearRepository):
        self.years = years

    def __call__(self, actor: Actor, query: GetYear) -> YearView:
        return year_view(load_year(self.years, actor.org_id, query.year_id))
