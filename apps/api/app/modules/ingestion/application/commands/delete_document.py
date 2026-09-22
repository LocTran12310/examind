from dataclasses import dataclass
import uuid

from app.modules.ingestion.application.common import load_document
from app.modules.ingestion.domain.ports import DocumentRepository, FileStorage, QuestionBank
from app.modules.ingestion.domain.services.documents import KEEP_ON_REPARSE
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class DeleteDocument:
    document_id: uuid.UUID


class DeleteDocumentHandler:
    """The file goes; approved questions stay in the bank (without their source), the others go with it and
    their duplicates go back to review."""

    def __init__(self, documents: DocumentRepository, files: FileStorage, bank: QuestionBank, audit: AuditTrail, uow: UnitOfWork):
        self.documents, self.files, self.bank, self.audit, self.uow = documents, files, bank, audit, uow

    def __call__(self, actor: Actor, cmd: DeleteDocument) -> None:
        doc = load_document(self.documents, actor.org_id, cmd.document_id)
        self.bank.remove_document_questions(doc.id, KEEP_ON_REPARSE, keep_used=False)
        self.files.delete(doc.storage_key)  # object storage cleanup is best effort
        self.audit.record(actor, actor.org_id, "document.delete", "document", doc.id, filename=doc.filename)
        self.documents.remove(doc)
        self.uow.commit()
