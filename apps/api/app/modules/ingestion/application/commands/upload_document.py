from dataclasses import dataclass
import hashlib
import uuid

from app.modules.ingestion.application.commands.reparse_document import ReparseDocument, ReparseDocumentHandler
from app.modules.ingestion.application.commands.update_document_meta import UpdateDocumentMeta, UpdateDocumentMetaHandler
from app.modules.ingestion.application.common import INGEST_JOB, config_for, ingest_payload, load_document, meta_for, not_busy
from app.modules.ingestion.domain.entities import SourceDocument
from app.modules.ingestion.domain.ports import DocumentRepository, FileStorage, OrgSettings, Taxonomy
from app.modules.ingestion.domain.services.documents import check_upload, detect_kind, display_name, storage_key
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.jobs import JobQueue
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.ids import new_id


@dataclass(frozen=True)
class UploadDocument:
    filename: str
    data: bytes
    meta: dict
    config: dict
    on_duplicate: str = "skip"  # skip | replace | keep_both
    replace_id: uuid.UUID | None = None


class UploadDocumentHandler:
    """Returns (document, action) with action created | skipped | reparsed | replaced.

    The same content is never stored twice: `skip` returns the existing document, `replace` re-parses it.
    A different file with the name of an existing one is added (`keep_both`, `skip` when no target) or
    replaces the chosen document's file (`replace` + `replace_id`), keeping approved and exam questions.
    """

    def __init__(self, documents: DocumentRepository, files: FileStorage, settings: OrgSettings, taxonomy: Taxonomy,
                 jobs: JobQueue, audit: AuditTrail, reparse: ReparseDocumentHandler, update_meta: UpdateDocumentMetaHandler,
                 uow: UnitOfWork):
        self.documents, self.files, self.settings, self.taxonomy, self.jobs, self.audit = documents, files, settings, taxonomy, jobs, audit
        self.reparse, self.update_meta, self.uow = reparse, update_meta, uow

    def __call__(self, actor: Actor, cmd: UploadDocument) -> tuple[SourceDocument, str]:
        check_upload(cmd.data, cmd.on_duplicate)
        kind, mime = detect_kind(cmd.filename, cmd.data)
        digest = hashlib.sha256(cmd.data).hexdigest()
        existing = self.documents.by_hash(actor.org_id, digest)
        if existing:
            if cmd.on_duplicate == "replace":
                self.reparse(actor, ReparseDocument(existing.id, cmd.config or None), commit=False)
                if cmd.meta:
                    kept = {k: v for k, v in (existing.meta or {}).items() if k != "detected"}
                    self.update_meta(actor, UpdateDocumentMeta(existing.id, {**kept, **cmd.meta}), commit=False)
                self.uow.commit()
                return existing, "reparsed"
            return existing, "skipped"
        if cmd.on_duplicate == "replace" and cmd.replace_id:
            return self._replace(actor, cmd, kind, mime, digest), "replaced"

        doc_id = new_id()
        key = storage_key(actor.org_id, doc_id, cmd.filename)
        self.files.put(key, cmd.data, mime)
        doc = SourceDocument(id=doc_id, organization_id=actor.org_id, filename=display_name(cmd.filename), mime=mime, size=len(cmd.data),
                             file_hash=digest, storage_key=key, status="queued", meta=meta_for(self.taxonomy, actor.org_id, cmd.meta),
                             processing_config=config_for(self.settings, actor.org_id, cmd.config), uploaded_by=actor.user_id, log=[])
        self.documents.add(doc)
        self.jobs.enqueue(INGEST_JOB, ingest_payload(doc))
        self.audit.record(actor, actor.org_id, "document.upload", "document", doc.id, filename=doc.filename, kind=kind)
        self.uow.commit()
        return doc, "created"

    def _replace(self, actor: Actor, cmd: UploadDocument, kind: str, mime: str, digest: str) -> SourceDocument:
        target = load_document(self.documents, actor.org_id, cmd.replace_id)
        not_busy(target)
        old_key = target.storage_key
        key = storage_key(actor.org_id, target.id, cmd.filename, version=new_id().hex[:8])
        self.files.put(key, cmd.data, mime)
        target.filename, target.mime, target.size, target.file_hash, target.storage_key = display_name(cmd.filename), mime, len(cmd.data), digest, key
        if cmd.meta:
            target.meta = {**(target.meta or {}), **meta_for(self.taxonomy, actor.org_id, cmd.meta)}
        if cmd.config:
            target.processing_config = config_for(self.settings, actor.org_id, cmd.config)
        target.status, target.error, target.page_count = "queued", None, None
        self.jobs.enqueue(INGEST_JOB, ingest_payload(target))
        self.audit.record(actor, actor.org_id, "document.replace", "document", target.id, filename=target.filename, kind=kind)
        self.uow.commit()
        self.files.delete(old_key)  # the old file is only garbage now; cleanup is best effort
        return target
