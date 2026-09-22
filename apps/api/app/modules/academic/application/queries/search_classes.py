from dataclasses import dataclass
import uuid

from app.modules.academic.application.dto import ClassView
from app.modules.academic.application.ports import ClassReader
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest


@dataclass(frozen=True)
class SearchClasses:
    request: SearchRequest
    school_year_id: uuid.UUID | None = None  # the year chosen in the header
    grade_id: uuid.UUID | None = None  # a khối of the structure tree


class SearchClassesHandler:
    def __init__(self, reader: ClassReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: SearchClasses) -> Page[ClassView]:
        return self.reader.search(actor.org_id, query.request, query.school_year_id, query.grade_id)
