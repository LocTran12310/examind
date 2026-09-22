from dataclasses import dataclass
import uuid

from app.modules.ingestion.application.common import load_document
from app.modules.ingestion.domain.ports import DocumentRepository, ExamDrafts
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class CreateExamFromDocument:
    document_id: uuid.UUID
    title: str | None = None


class CreateExamFromDocumentHandler:
    """A draft exam with the document's usable questions in the original PHẦN / Câu order (AC-11, AC-12);
    the exam itself belongs to the assessment context."""

    def __init__(self, documents: DocumentRepository, exams: ExamDrafts, uow: UnitOfWork):
        self.documents, self.exams, self.uow = documents, exams, uow

    def __call__(self, actor: Actor, cmd: CreateExamFromDocument) -> dict:
        doc = load_document(self.documents, actor.org_id, cmd.document_id)
        out = self.exams.from_document(actor, doc.id, doc.filename, doc.status, doc.meta or {}, cmd.title)
        self.uow.commit()
        return out
