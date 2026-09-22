"""Helpers shared by the ingestion handlers."""
import uuid

from app.modules.ingestion.domain.entities import SourceDocument
from app.modules.ingestion.domain.ports import DocumentRepository, OrgSettings, Taxonomy
from app.modules.ingestion.domain.services.documents import clean_meta
from app.modules.ingestion.domain.services.processing import org_defaults, resolve_config
from app.shared.domain.errors import Conflict, NotFound


def load_document(documents: DocumentRepository, org_id: uuid.UUID, document_id: uuid.UUID) -> SourceDocument:
    doc = documents.get(org_id, document_id)
    if doc is None:
        raise NotFound("Không tìm thấy tài liệu")
    return doc


def not_busy(doc: SourceDocument) -> None:
    if doc.busy:
        raise Conflict("Tài liệu đang được xử lý", code="busy")


def config_for(settings: OrgSettings, org_id: uuid.UUID, override: dict | None) -> dict:
    """upload choice > org default > system default"""
    return resolve_config(org_defaults(settings.ingestion(org_id)), override)


def meta_for(taxonomy: Taxonomy, org_id: uuid.UUID, meta: dict) -> dict:
    return clean_meta(meta, lambda sid: taxonomy.subject_in_org(org_id, sid), lambda: taxonomy.semester_codes(org_id))


INGEST_JOB = "ingest_document"


def ingest_payload(doc: SourceDocument) -> dict:
    return {"document_id": str(doc.id)}
