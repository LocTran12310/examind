from dataclasses import dataclass

from app.modules.identity.application.dto import OrgView
from app.modules.identity.application.ports import OrgReader
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchOrgs:
    request: SearchRequest
    include_deleted: bool = False


class SearchOrgsHandler:
    def __init__(self, reader: OrgReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchOrgs) -> Page[OrgView]:
        return self.reader.search(query.request, query.include_deleted)
