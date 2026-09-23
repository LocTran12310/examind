from dataclasses import dataclass

from app.modules.bank.application.dto import EventBatchView
from app.modules.bank.application.ports import EventReader
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchQuestionEvents:
    request: SearchRequest


class SearchQuestionEventsHandler:
    """"Thay đổi gần đây": the bank's recent changes, one row per request (A-05), of the caller's organisation only."""

    def __init__(self, reader: EventReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchQuestionEvents) -> Page[EventBatchView]:
        return self.reader.batches(actor.org_id, query.request)
