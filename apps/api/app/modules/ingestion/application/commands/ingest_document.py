"""Ingestion pipeline run by the worker: extract → header → split → (AI fallback) → persist → triage → suggest (ADR-02)."""
from collections.abc import Callable
from dataclasses import dataclass
import uuid

import structlog

from app.modules.ingestion.application.run import IngestRun
from app.modules.ingestion.application.stages.ai_split import AiSplitter
from app.modules.ingestion.application.stages.extract import Extractor
from app.modules.ingestion.application.stages.topic_suggest import Stored, TopicSuggester
from app.modules.ingestion.domain.errors import IngestError
from app.modules.ingestion.domain.ports import DocumentRepository, FileStorage, ImageStore, QuestionBank, Taxonomy
from app.modules.ingestion.domain.services import header
from app.modules.ingestion.domain.services.documents import KEEP_ON_REPARSE
from app.modules.ingestion.domain.services.splitter import ParsedQuestion, split
from app.shared.application.unit_of_work import UnitOfWork

log = structlog.get_logger("ingest")

ImageStores = Callable[[object, list[str], dict], ImageStore]  # (document, warnings, stats) -> ImageStore


@dataclass(frozen=True)
class IngestDocument:
    document_id: str


@dataclass(frozen=True)
class MarkIngestFailed:
    document_id: str
    error: str


def draft_of(p: ParsedQuestion, meta: dict) -> dict:
    """The bank columns of a parsed question; the document's meta gives subject, grade, đợt and loại đề."""
    return dict(
        subject_id=uuid.UUID(meta["subject_id"]) if meta.get("subject_id") else None,
        type=p.type, stem=p.stem, options=p.options, answer=p.answer, solution=p.solution,
        grade=meta.get("grade"), semester_code=meta.get("semester_code"), exam_kind=meta.get("exam_kind"),
        status="draft", source="document", number=p.number, part=p.part,
        page=p.pages[0] if p.pages else None,
        confidence=p.confidence, issues=p.issues, parse_method=getattr(p, "parse_method", None) or ("ocr" if p.ocr else "rule"),
        parse_model=getattr(p, "parse_model", None), answer_source=p.answer_source,
    )


class IngestDocumentHandler:
    """Commits twice: `processing` first (the teacher sees it), then the outcome. A failure fit for the teacher
    (IngestError) is recorded on the document; anything else propagates so the job queue retries."""

    def __init__(self, documents: DocumentRepository, files: FileStorage, images: ImageStores, extract: Extractor,
                 ai: AiSplitter, taxonomy: Taxonomy, bank: QuestionBank, topics: TopicSuggester, clock, uow: UnitOfWork):
        self.documents, self.files, self.images, self.extract, self.ai = documents, files, images, extract, ai
        self.taxonomy, self.bank, self.topics, self.clock, self.uow = taxonomy, bank, topics, clock, uow

    def __call__(self, cmd: IngestDocument) -> None:
        doc_id = uuid.UUID(cmd.document_id)
        doc = self.documents.get_any(doc_id)
        if doc is None:
            return
        doc.status, doc.error = "processing", None
        self.uow.commit()
        run = IngestRun(doc)
        try:
            data, _ = self.files.get(doc.storage_key)
            run.step("download", bytes=len(data))
            lines = self.extract(data, self.images(doc, run.warnings, run.stats), run)
            run.lines = lines
            run.step("extract", lines=len(lines), pages=doc.page_count, **run.stats)
            # doc.meta["detected"]; fills fields the uploader left empty
            header.apply(doc, lines, self.taxonomy.subjects(doc.organization_id))
            result = split(lines)
            run.warnings += result.warnings
            run.step("split", questions=len(result.questions))
            self.ai.stage(result.questions, run)
            rows, kept = self._persist(doc, result.questions)
            run.step("persist", questions=len(rows))
            # triage first: it fills search_text that topic suggestion (kNN) reads
            threshold = float((doc.processing_config or {}).get("threshold", 0.85))
            counts = self.bank.triage([q.id for _, q in rows], threshold, str(doc.id))
            run.step("triage", **counts)
            self.topics(doc, rows, run)
            doc.status = "parsed"
            doc.question_count = len(rows) + kept  # questions kept from a previous parse still belong to it
            if not rows and not kept:
                run.warnings.append("Không tìm thấy câu hỏi nào — kiểm tra định dạng 'Câu 1.' hoặc thử chế độ AI")
        except IngestError as exc:
            self.uow.rollback()
            doc = self.documents.get_any(doc_id)
            doc.status, doc.error = "failed", str(exc)
            run.step("failed", error=str(exc))
        doc.log = run.log + ([{"step": "warnings", "items": run.warnings}] if run.warnings else [])
        doc.finished_at = self.clock()
        self.uow.commit()
        log.info("ingest.done", document=cmd.document_id, status=doc.status, questions=doc.question_count)

    def _persist(self, doc, parsed: list[ParsedQuestion]) -> tuple[list[tuple[ParsedQuestion, Stored]], int]:
        """(new questions, how many earlier ones were kept)."""
        # approved questions and questions already used in an exam survive a re-parse (A-14)
        self.bank.remove_document_questions(doc.id, KEEP_ON_REPARSE, keep_used=True)
        kept = self.bank.kept_positions(doc.id)
        meta = doc.meta or {}
        tag_id = self.taxonomy.source_tag(doc.organization_id, meta.get("source_name"))
        fresh = [p for p in parsed if (p.part, p.number) not in kept]  # an approved question from a previous parse wins (A-14)
        ids = self.bank.add_parsed(doc.organization_id, doc.id, [draft_of(p, meta) for p in fresh], tag_id)
        return [(p, Stored(qid, p.stem, p.options)) for p, qid in zip(fresh, ids)], len(kept)


class MarkIngestFailedHandler:
    """The job failed for good (crash after the last retry): tell the teacher without the traceback."""

    def __init__(self, documents: DocumentRepository, clock, uow: UnitOfWork):
        self.documents, self.clock, self.uow = documents, clock, uow

    def __call__(self, cmd: MarkIngestFailed) -> None:
        doc = self.documents.get_any(uuid.UUID(cmd.document_id))
        if doc is None:
            return
        doc.status = "failed"
        doc.error = "Lỗi khi xử lý file, vui lòng thử lại hoặc báo quản trị viên"
        doc.log = (doc.log or []) + [{"step": "crashed", "error": cmd.error.splitlines()[0][:300]}]
        doc.finished_at = self.clock()
        self.uow.commit()
