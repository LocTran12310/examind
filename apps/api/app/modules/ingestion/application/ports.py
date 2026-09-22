"""Read ports of ingestion (lists)."""
from typing import Protocol
import uuid

from app.modules.ingestion.domain.entities import AiModel, SourceDocument
from app.shared.application.search import Page, SearchRequest


class DocumentReader(Protocol):
    def search(self, org_id: uuid.UUID, req: SearchRequest) -> Page[SourceDocument]:
        """Newest first. Filters: filename, source_name (text) · status, mime (enum) · question_count (number) · created_at (date);
        `q` over filename and source name."""
        ...


class AiModelReader(Protocol):
    def search(self, org_id: uuid.UUID | None, req: SearchRequest) -> Page[AiModel]:
        """The org's models and the system ones (org_id None: the system ones only), system first then by name.
        Filters: name, model (text) · provider (enum) · enabled, is_free (bool)."""
        ...
