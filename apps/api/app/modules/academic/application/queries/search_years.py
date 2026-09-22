from dataclasses import dataclass

from app.modules.academic.application.dto import YearView
from app.modules.academic.application.ports import YearReader
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchYears:
    request: SearchRequest


class SearchYearsHandler:
    def __init__(self, reader: YearReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchYears) -> Page[YearView]:
        return self.reader.search(actor.org_id, query.request)
