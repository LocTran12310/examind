from dataclasses import dataclass
import uuid

from app.modules.academic.application.ports import StructureReader
from app.shared.application.actor import Actor


@dataclass(frozen=True)
class StructureTree:
    school_year: str | None = None
    school_year_id: uuid.UUID | None = None


class StructureTreeHandler:
    """Cấp học › Khối › Lớp with class and student counts, for one year's classes (or all)."""

    def __init__(self, reader: StructureReader):
        self.reader = reader

    def __call__(self, actor: Actor, query: StructureTree) -> dict:
        return self.reader.tree(actor.org_id, query.school_year, query.school_year_id)
