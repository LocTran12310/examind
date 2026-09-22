from datetime import datetime
import uuid

from pydantic import BaseModel

from app.modules.bank.interface.schemas import ParsedQuestionOut, TagRef, TopicRef  # noqa: F401  (moved to the bank module)


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
    action: str = "created"  # created | skipped | reparsed | replaced


class FileProbe(BaseModel):
    name: str
    size: int | None = None
    sha256: str


class DuplicateCheckIn(BaseModel):
    files: list[FileProbe]


class DocumentBrief(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    question_count: int
    created_at: datetime


class DuplicateOut(BaseModel):
    name: str
    same_file: DocumentBrief | None
    same_name: list[DocumentBrief]


class ReparseIn(BaseModel):
    config: dict | None = None


class DocumentMetaIn(BaseModel):
    meta: dict


def document_out(d) -> DocumentOut:
    return DocumentOut(id=d.id, filename=d.filename, mime=d.mime, size=d.size, status=d.status, error=d.error, meta=d.meta or {},
                       processing_config=d.processing_config or {}, page_count=d.page_count, question_count=d.question_count,
                       log=d.log or [], created_at=d.created_at, finished_at=d.finished_at)
