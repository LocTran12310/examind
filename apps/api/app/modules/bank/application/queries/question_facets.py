from dataclasses import dataclass

from app.modules.bank.application.common import resolve_filters
from app.modules.bank.application.dto import BankFilters
from app.modules.bank.application.ports import QuestionReader
from app.modules.bank.domain.ports import Taxonomy
from app.shared.application.actor import Actor
from app.shared.application.search import SearchRequest


@dataclass(frozen=True)
class QuestionFacets:
    request: SearchRequest
    filters: BankFilters


class QuestionFacetsHandler:
    """Counts for the filter sheet (subject-scoped-bank ADR-02): each facet applies every filter but its own."""

    def __init__(self, reader: QuestionReader, taxonomy: Taxonomy):
        self.reader, self.taxonomy = reader, taxonomy

    def __call__(self, actor: Actor, query: QuestionFacets) -> dict[str, dict[str, int]]:
        return self.reader.facets(actor.org_id, query.request, resolve_filters(self.taxonomy, actor.org_id, query.filters))
