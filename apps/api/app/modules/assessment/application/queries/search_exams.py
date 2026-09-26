from dataclasses import dataclass
import uuid

from app.modules.assessment.application.dto import ExamSummary
from app.modules.assessment.application.ports import ExamReader
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchExams:
    request: SearchRequest
    subject_id: uuid.UUID | str | None = None


class SearchExamsHandler:
    def __init__(self, reader: ExamReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchExams) -> Page[ExamSummary]:
        return self.reader.search(actor.org_id, query.request, query.subject_id)


class ExamFacetsHandler:
    """How many exams each subject holds under the current search — the numbers the subject tabs carry."""

    def __init__(self, reader: ExamReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchExams) -> dict[str, dict[str, int]]:
        return {"subjects": self.reader.subject_counts(actor.org_id, query.request)}
