from dataclasses import dataclass

from app.modules.taxonomy.application.dto import TagView
from app.modules.taxonomy.application.ports import TagReader
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchTags:
    request: SearchRequest
    subject: str | None = None
    include_shared: bool = True


class SearchTagsHandler:
    def __init__(self, reader: TagReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchTags) -> Page[TagView]:
        return self.reader.search(actor.org_id, query.request, query.subject, query.include_shared)
