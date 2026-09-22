from dataclasses import dataclass

from app.modules.bank.application.dto import QuestionView
from app.modules.bank.application.ports import QuestionViews, ReviewReader
from app.modules.bank.domain.services.review import FLAGGED_GROUP
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchFlagged:
    request: SearchRequest


class SearchFlaggedHandler:
    """Questions whose answer key the audit suspects, with the evidence."""

    def __init__(self, reader: ReviewReader, views: QuestionViews):
        self.reader, self.views = reader, views

    def __call__(self, actor: Actor, query: SearchFlagged) -> Page[QuestionView]:
        page = self.reader.flagged(actor.org_id, query.request)
        return Page(self.views.views(page.data, {q.id: FLAGGED_GROUP for q in page.data}), page.total, page.page, page.limit)
