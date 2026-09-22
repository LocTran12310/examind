"""Uploaded exam files moved to the ingestion module (architecture-refactor UOW-05); the exam builder (old layout)
still looks a document up here."""
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.modules.ingestion.domain.entities import SourceDocument
from app.modules.ingestion.domain.services.documents import KEEP_ON_REPARSE  # noqa: F401
from app.modules.ingestion.infrastructure.repositories import SqlDocumentRepository


def get_document(db: Session, scope, doc_id) -> SourceDocument:
    doc = SqlDocumentRepository(db).get(scope.org_id, doc_id)
    if doc is None:
        raise not_found("Không tìm thấy tài liệu")
    return doc
