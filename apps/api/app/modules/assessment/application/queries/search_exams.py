from dataclasses import dataclass

from app.modules.assessment.application.dto import ExamSummary
from app.modules.assessment.application.ports import ExamReader
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchExams:
    request: SearchRequest


class SearchExamsHandler:
    def __init__(self, reader: ExamReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchExams) -> Page[ExamSummary]:
        return self.reader.search(actor.org_id, query.request)
