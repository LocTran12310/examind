from dataclasses import dataclass
import uuid

from app.modules.ingestion.application.common import load_document, meta_for
from app.modules.ingestion.domain.entities import SourceDocument
from app.modules.ingestion.domain.ports import DocumentRepository, QuestionBank, Taxonomy
from app.modules.ingestion.domain.services.documents import QUESTION_META
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class UpdateDocumentMeta:
    document_id: uuid.UUID
    meta: dict


class UpdateDocumentMetaHandler:
    """Edit subject / grade / đợt / năm học / nguồn after upload (e.g. confirm the detected header);
    the document's questions follow, including the source tag."""

    def __init__(self, documents: DocumentRepository, taxonomy: Taxonomy, bank: QuestionBank, audit: AuditTrail, uow: UnitOfWork):
        self.documents, self.taxonomy, self.bank, self.audit, self.uow = documents, taxonomy, bank, audit, uow

    def __call__(self, actor: Actor, cmd: UpdateDocumentMeta, commit: bool = True) -> SourceDocument:
        doc = load_document(self.documents, actor.org_id, cmd.document_id)
        old = dict(doc.meta or {})
        new = meta_for(self.taxonomy, actor.org_id, cmd.meta)
        if old.get("detected"):
            new["detected"] = old["detected"]
        doc.meta = new
        changes = {k: new.get(k) for k in QUESTION_META if new.get(k) != old.get(k)}
        old_tag = new_tag = None
        retag = new.get("source_name") != old.get("source_name")
        if retag:
            old_tag = self.taxonomy.source_tag(doc.organization_id, old.get("source_name"))
            new_tag = self.taxonomy.source_tag(doc.organization_id, new.get("source_name"))
        self.bank.follow_document(doc.id, changes, old_tag, new_tag)
        self.audit.record(actor, actor.org_id, "document.meta", "document", doc.id,
                          changes={k: v for k, v in new.items() if k != "detected" and v != old.get(k)})
        if commit:
            self.uow.commit()
        return doc
