"""What assessment knows of the other contexts' data: a bank question as an exam uses it, a student's school-year
snapshot, a source document an exam is drafted from."""
from dataclasses import dataclass, field
import uuid

USABLE = ("auto_approved", "approved")


@dataclass(frozen=True)
class QuestionRef:
    """A bank question as an exam sees it: content, answer key and the facts grading and reports need."""
    id: uuid.UUID
    organization_id: uuid.UUID
    type: str
    status: str
    stem: str = ""
    options: list = field(default_factory=list)
    answer: dict | None = None
    solution: str = ""
    difficulty: str | None = None
    grade: int | None = None
    part: str | None = None
    number: int | None = None
    source_document_id: uuid.UUID | None = None

    @property
    def usable(self) -> bool:
        return self.status in USABLE


@dataclass(frozen=True)
class Snapshot:
    """A student's school year, term and classes (of that year) at a moment (school-years ADR-02)."""
    school_year_id: uuid.UUID | None = None
    term_code: str | None = None
    class_ids: tuple[uuid.UUID, ...] = ()


@dataclass(frozen=True)
class DocumentRef:
    """A source document an exam is drafted from (ingestion hands it over)."""
    id: uuid.UUID
    filename: str
    status: str
    meta: dict = field(default_factory=dict)


@dataclass(frozen=True)
class PoolFilter:
    """The bank questions a blueprint row (or a swap) may draw from: usable ones, by these filters."""
    subject_id: uuid.UUID | None = None
    type: str | None = None
    difficulty: str | None = None
    topic_id: uuid.UUID | None = None
    tag_id: uuid.UUID | None = None
