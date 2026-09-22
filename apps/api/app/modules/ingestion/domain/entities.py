"""Ingestion context: an uploaded exam file and how it was processed, the images stored from files (and from the
editor), the AI models an org may use."""
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.shared.domain.ids import new_id

DOC_STATUSES = ("queued", "processing", "parsed", "failed")
BUSY = ("queued", "processing")
PROVIDERS = ("ollama", "openai", "anthropic")
CAPABILITIES = ("text", "vision")


@dataclass(eq=False)
class SourceDocument:
    organization_id: uuid.UUID
    filename: str
    mime: str
    size: int
    file_hash: str
    storage_key: str
    status: str = "queued"
    error: str | None = None
    meta: dict = field(default_factory=dict)  # column "metadata": subject_id, grade, semester_code, exam_kind, school_year, source_name, detected
    processing_config: dict = field(default_factory=dict)
    page_count: int | None = None
    question_count: int = 0
    log: list = field(default_factory=list)
    uploaded_by: uuid.UUID | None = None
    assigned_to: uuid.UUID | None = None
    finished_at: datetime | None = None
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None

    @property
    def kind(self) -> str:
        if self.mime == "application/pdf":
            return "pdf"
        if self.mime.startswith("image/"):
            return "image"
        return "docx"

    @property
    def busy(self) -> bool:
        return self.status in BUSY


@dataclass(eq=False)
class Asset:
    """An image stored in object storage, referenced from markdown as `asset:<id>`."""
    organization_id: uuid.UUID
    storage_key: str
    mime: str
    size: int
    width: int | None = None
    height: int | None = None
    source_document_id: uuid.UUID | None = None
    page: int | None = None
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None


@dataclass(eq=False)
class AiModel:
    """A model an org (or, with organization_id None, every org) may use for splitting, tagging or OCR."""
    name: str
    provider: str
    model: str
    organization_id: uuid.UUID | None = None
    base_url: str | None = None
    api_key_enc: str | None = None
    capabilities: list[str] = field(default_factory=lambda: ["text"])
    is_free: bool = True
    enabled: bool = True
    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime | None = None

    @property
    def system(self) -> bool:
        return self.organization_id is None

    def usable_by(self, org_id: uuid.UUID) -> bool:
        """Enabled and either the org's own or a system model."""
        return self.enabled and self.organization_id in (None, org_id)
