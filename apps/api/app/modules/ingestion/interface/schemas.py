from datetime import datetime
import uuid

from pydantic import BaseModel, Field


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


def document_out(d) -> DocumentOut:
    return DocumentOut(id=d.id, filename=d.filename, mime=d.mime, size=d.size, status=d.status, error=d.error, meta=d.meta or {},
                       processing_config=d.processing_config or {}, page_count=d.page_count, question_count=d.question_count,
                       log=d.log or [], created_at=d.created_at, finished_at=d.finished_at)


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


class ExamFromDocumentIn(BaseModel):
    title: str | None = None


class AssetOut(BaseModel):
    id: uuid.UUID
    mime: str
    width: int | None
    height: int | None
    ref: str


class AiModelIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    provider: str
    model: str = Field(min_length=1, max_length=120)
    base_url: str | None = Field(default=None, max_length=300)
    api_key: str | None = Field(default=None, max_length=500)
    capabilities: list[str] = ["text"]
    is_free: bool = True
    enabled: bool = True


class AiModelUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    provider: str | None = None
    model: str | None = Field(default=None, max_length=120)
    base_url: str | None = Field(default=None, max_length=300)
    api_key: str | None = Field(default=None, max_length=500)  # "" clears the key
    capabilities: list[str] | None = None
    is_free: bool | None = None
    enabled: bool | None = None


class AiModelOut(BaseModel):
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


class DiscoverIn(BaseModel):
    base_url: str | None = None


class TestResult(BaseModel):
    ok: bool
    latency_ms: int | None = None
    error: str | None = None
    sample: str | None = None
