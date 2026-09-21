from datetime import datetime
import uuid

from pydantic import BaseModel

from app.schemas.questions import QuestionOut


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    mime: str
    size: int
    status: str
    error: str | None
    meta: dict
    processing_config: dict
    page_count: int | None
    question_count: int
    log: list
    created_at: datetime
    finished_at: datetime | None


class DocumentCreated(BaseModel):
    document: DocumentOut
    duplicate: bool


class TopicRef(BaseModel):
    id: uuid.UUID
    name: str
    is_primary: bool
    source: str
    score: float | None


class TagRef(BaseModel):
    id: uuid.UUID
    group: str
    name: str


class ParsedQuestionOut(QuestionOut):
    number: int | None
    part: str | None
    confidence: float | None
    issues: list
    parse_method: str | None
    parse_model: str | None
    answer_source: str | None
    subject_id: uuid.UUID | None
    semester_code: str | None
    exam_kind: str | None
    topics: list[TopicRef] = []
    tags: list[TagRef] = []
    page: int | None = None
    spot_check: bool = False
    duplicate_of: uuid.UUID | None = None
    source_document_id: uuid.UUID | None = None
    group: str | None = None


class ReparseIn(BaseModel):
    config: dict | None = None


def document_out(d) -> DocumentOut:
    return DocumentOut(id=d.id, filename=d.filename, mime=d.mime, size=d.size, status=d.status, error=d.error, meta=d.meta or {},
                       processing_config=d.processing_config or {}, page_count=d.page_count, question_count=d.question_count,
                       log=d.log or [], created_at=d.created_at, finished_at=d.finished_at)
