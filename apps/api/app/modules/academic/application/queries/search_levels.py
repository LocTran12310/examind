from dataclasses import dataclass

from app.modules.academic.application.dto import LevelView
from app.modules.academic.application.ports import LevelReader
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchLevels:
    request: SearchRequest


class SearchLevelsHandler:
    def __init__(self, reader: LevelReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchLevels) -> Page[LevelView]:
        return self.reader.search(actor.org_id, query.request)
