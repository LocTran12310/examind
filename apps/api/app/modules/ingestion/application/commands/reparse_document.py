from dataclasses import dataclass
import uuid

from app.modules.ingestion.application.common import INGEST_JOB, config_for, ingest_payload, load_document, not_busy
from app.modules.ingestion.domain.entities import SourceDocument
from app.modules.ingestion.domain.ports import DocumentRepository, OrgSettings
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.jobs import JobQueue
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class ReparseDocument:
    document_id: uuid.UUID
    config: dict | None = None  # None keeps the document's config


class ReparseDocumentHandler:
    """Queue the document again; approved and exam questions survive the new parse (A-14)."""

    def __init__(self, documents: DocumentRepository, settings: OrgSettings, jobs: JobQueue, audit: AuditTrail, uow: UnitOfWork):
        self.documents, self.settings, self.jobs, self.audit, self.uow = documents, settings, jobs, audit, uow

    def __call__(self, actor: Actor, cmd: ReparseDocument, commit: bool = True) -> SourceDocument:
        doc = load_document(self.documents, actor.org_id, cmd.document_id)
        not_busy(doc)
        if cmd.config is not None:
            doc.processing_config = config_for(self.settings, actor.org_id, cmd.config)
        doc.status, doc.error = "queued", None
        self.jobs.enqueue(INGEST_JOB, ingest_payload(doc))
        self.audit.record(actor, actor.org_id, "document.reparse", "document", doc.id)
        if commit:
            self.uow.commit()
        return doc
