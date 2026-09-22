from dataclasses import dataclass

from app.modules.bank.application.dto import ReviewDocumentView
from app.modules.bank.application.ports import ReviewReader
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchReviewDocuments:
    request: SearchRequest
    mine: bool = False  # only the documents given to the caller


class SearchReviewDocumentsHandler:
    def __init__(self, reader: ReviewReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchReviewDocuments) -> Page[ReviewDocumentView]:
        return self.reader.search_documents(actor.org_id, query.request, actor.user_id if query.mine else None)
