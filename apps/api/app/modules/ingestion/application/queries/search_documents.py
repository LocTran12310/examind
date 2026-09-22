from dataclasses import dataclass

from app.modules.ingestion.application.ports import DocumentReader
from app.modules.ingestion.domain.entities import SourceDocument
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchDocuments:
    request: SearchRequest


class SearchDocumentsHandler:
    def __init__(self, reader: DocumentReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchDocuments) -> Page[SourceDocument]:
        return self.reader.search(actor.org_id, query.request)
