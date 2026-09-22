from dataclasses import dataclass
import uuid

from app.modules.ingestion.application.common import load_document
from app.modules.ingestion.application.dto import FileContent
from app.modules.ingestion.domain.entities import SourceDocument
from app.modules.ingestion.domain.ports import DocumentRepository, FileStorage, PageRenderer
from app.modules.ingestion.domain.services.documents import page_key
from app.shared.application.actor import Actor
from app.shared.domain.errors import NotFound


@dataclass(frozen=True)
class GetDocument:
    document_id: uuid.UUID


class GetDocumentHandler:
    def __init__(self, documents: DocumentRepository):
        self.documents = documents

    def __call__(self, actor: Actor, query: GetDocument) -> SourceDocument:
        return load_document(self.documents, actor.org_id, query.document_id)


class DocumentFileHandler:
    """The uploaded file as it was sent."""

    def __init__(self, documents: DocumentRepository, files: FileStorage):
        self.documents, self.files = documents, files

    def __call__(self, actor: Actor, query: GetDocument) -> FileContent:
        doc = load_document(self.documents, actor.org_id, query.document_id)
        data, _ = self.files.get(doc.storage_key)
        return FileContent(data, doc.mime, doc.filename)


@dataclass(frozen=True)
class GetPageImage:
    document_id: uuid.UUID
    page: int


class PageImageHandler:
    """Source page for the review queue: PDFs rendered once and cached in object storage; images served as-is.
    Returns (content, cached-forever)."""

    def __init__(self, documents: DocumentRepository, files: FileStorage, renderer: PageRenderer):
        self.documents, self.files, self.renderer = documents, files, renderer

    def __call__(self, actor: Actor, query: GetPageImage) -> tuple[FileContent, bool]:
        doc = load_document(self.documents, actor.org_id, query.document_id)
        page = query.page
        if doc.mime.startswith("image/") and page == 1:
            data, mime = self.files.get(doc.storage_key)
            return FileContent(data, mime), False
        if doc.mime != "application/pdf" or page < 1 or (doc.page_count and page > doc.page_count):
            raise NotFound("Không có ảnh trang")
        key = page_key(doc.storage_key, page)
        try:
            data, _ = self.files.get(key)
        except Exception:
            raw, _ = self.files.get(doc.storage_key)
            data = self.renderer.render_png(raw, page)
            self.files.put(key, data, "image/png")
        return FileContent(data, "image/png"), True
