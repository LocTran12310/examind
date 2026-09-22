from dataclasses import dataclass
from datetime import datetime
import uuid

from app.modules.ingestion.domain.entities import SourceDocument


@dataclass(frozen=True)
class DocumentBrief:
    id: uuid.UUID
    filename: str
    status: str
    question_count: int
    created_at: datetime


def brief(d: SourceDocument) -> DocumentBrief:
    return DocumentBrief(id=d.id, filename=d.filename, status=d.status, question_count=d.question_count, created_at=d.created_at)


@dataclass(frozen=True)
class DuplicateReport:
    """For one file about to be uploaded: the document with the same content, documents with the same name."""
    name: str
    same_file: DocumentBrief | None
    same_name: list[DocumentBrief]


@dataclass(frozen=True)
class FileContent:
    data: bytes
    mime: str
    filename: str | None = None


@dataclass(frozen=True)
class AiModelView:
    id: uuid.UUID
    name: str
    provider: str
    model: str
    base_url: str | None
    capabilities: list[str]
    is_free: bool
    enabled: bool
    system: bool
    has_key: bool
    editable: bool
