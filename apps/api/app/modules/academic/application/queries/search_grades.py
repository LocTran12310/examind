from dataclasses import dataclass
import uuid

from app.modules.academic.application.dto import GradeView
from app.modules.academic.application.ports import GradeReader
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchGrades:
    request: SearchRequest
    school_level_id: uuid.UUID | None = None


class SearchGradesHandler:
    def __init__(self, reader: GradeReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchGrades) -> Page[GradeView]:
        return self.reader.search(actor.org_id, query.request, query.school_level_id)
