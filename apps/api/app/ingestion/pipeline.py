"""Ingestion pipeline run by the worker: extract → split → (AI fallback) → persist → suggest (ADR-02)."""
from collections.abc import Callable
import time
import uuid

import structlog
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core import storage
from app.core.security import now
from app.ingestion.assets import document_store
from app.ingestion.lines import Line
from app.ingestion.splitter import ParsedQuestion, split
from app.models import Question, QuestionTag, SourceDocument, Tag
from app.services.documents import KEEP_ON_REPARSE

log = structlog.get_logger("ingest")


class IngestError(Exception):
    """A failure with a message fit for the teacher."""


# Stages later tickets plug in (PDF/OCR extractors, AI fallback, topic suggestion).
EXTRACTORS: dict[str, Callable] = {}
POST_SPLIT: list[Callable] = []     # fn(db, doc, questions, ctx) -> None, may rewrite ParsedQuestions
POST_PERSIST: list[Callable] = []   # fn(db, doc, rows: list[tuple[ParsedQuestion, Question]], ctx) -> None


class Ctx:
    def __init__(self, doc: SourceDocument, db: Session | None = None):
        self.doc = doc
        self.db = db
        self.warnings: list[str] = []
        self.lines: list[Line] = []
        self.log: list[dict] = []
        self._t = time.monotonic()

    def step(self, name: str, **data) -> None:
        t = time.monotonic()
        self.log.append({"step": name, "ms": int((t - self._t) * 1000), **data})
        self._t = t


def _kind(doc: SourceDocument) -> str:
    if doc.mime == "application/pdf":
        return "pdf"
    if doc.mime.startswith("image/"):
        return "image"
    return "docx"


def extract(db: Session, doc: SourceDocument, data: bytes, ctx: Ctx) -> list[Line]:
    kind = _kind(doc)
    store = document_store(db, doc.organization_id, doc.id, ctx.warnings)
    if kind == "docx":
        from app.ingestion.docx import DocxError, extract_docx

        try:
            lines, warnings = extract_docx(data, store)
        except DocxError as exc:
            raise IngestError(str(exc)) from exc
        ctx.warnings += warnings
        return lines
    fn = EXTRACTORS.get(kind)
    if fn is None:
        raise IngestError(f"Chưa hỗ trợ đọc loại file này ({kind})")
    return fn(db, doc, data, store, ctx)


def ingest(db: Session, document_id: str) -> None:
    doc = db.get(SourceDocument, uuid.UUID(document_id))
    if doc is None:
        return
    doc.status, doc.error = "processing", None
    db.commit()
    ctx = Ctx(doc, db)
    try:
        data, _ = storage.get(doc.storage_key)
        ctx.step("download", bytes=len(data))
        lines = extract(db, doc, data, ctx)
        ctx.lines = lines
        ctx.step("extract", lines=len(lines), pages=doc.page_count)
        result = split(lines)
        ctx.warnings += result.warnings
        ctx.step("split", questions=len(result.questions))
        for fn in POST_SPLIT:
            fn(db, doc, result.questions, ctx)
        rows = persist(db, doc, result.questions)
        ctx.step("persist", questions=len(rows))
        for fn in POST_PERSIST:
            fn(db, doc, rows, ctx)
        doc.status = "parsed"
        doc.question_count = len(rows)
        if not rows:
            ctx.warnings.append("Không tìm thấy câu hỏi nào — kiểm tra định dạng 'Câu 1.' hoặc thử chế độ AI")
    except IngestError as exc:
        db.rollback()
        doc = db.get(SourceDocument, uuid.UUID(document_id))
        doc.status, doc.error = "failed", str(exc)
        ctx.step("failed", error=str(exc))
    doc.log = ctx.log + ([{"step": "warnings", "items": ctx.warnings}] if ctx.warnings else [])
    doc.finished_at = now()
    db.commit()
    log.info("ingest.done", document=document_id, status=doc.status, questions=doc.question_count)


def mark_failed(db: Session, document_id: str, error: str) -> None:
    doc = db.get(SourceDocument, uuid.UUID(document_id))
    if doc is None:
        return
    doc.status = "failed"
    doc.error = "Lỗi khi xử lý file, vui lòng thử lại hoặc báo quản trị viên"
    doc.log = (doc.log or []) + [{"step": "crashed", "error": error.splitlines()[0][:300]}]
    doc.finished_at = now()
    db.commit()


def persist(db: Session, doc: SourceDocument, parsed: list[ParsedQuestion]) -> list[tuple[ParsedQuestion, Question]]:
    db.execute(delete(Question).where(Question.source_document_id == doc.id, Question.status.notin_(KEEP_ON_REPARSE)))
    kept = {(q.part, q.number) for q in db.scalars(select(Question).where(Question.source_document_id == doc.id))}
    meta = doc.meta or {}
    tag = _source_tag(db, doc.organization_id, meta.get("source_name"))
    rows = []
    for p in parsed:
        if (p.part, p.number) in kept:
            continue  # an approved question from a previous parse wins (A-14)
        q = Question(
            organization_id=doc.organization_id,
            subject_id=uuid.UUID(meta["subject_id"]) if meta.get("subject_id") else None,
            type=p.type, stem=p.stem, options=p.options, answer=p.answer, solution=p.solution,
            grade=meta.get("grade"), semester_code=meta.get("semester_code"), exam_kind=meta.get("exam_kind"),
            status="draft", source="document", source_document_id=doc.id, number=p.number, part=p.part,
            page=p.pages[0] if p.pages else None,
            confidence=p.confidence, issues=p.issues, parse_method=getattr(p, "parse_method", None) or ("ocr" if p.ocr else "rule"),
            parse_model=getattr(p, "parse_model", None), answer_source=p.answer_source,
        )
        db.add(q)
        rows.append((p, q))
    db.flush()
    if tag:
        for _, q in rows:
            db.add(QuestionTag(question_id=q.id, tag_id=tag.id))
    db.flush()
    return rows


def _source_tag(db: Session, org_id, name: str | None) -> Tag | None:
    if not name:
        return None
    from sqlalchemy import func

    tag = db.scalar(select(Tag).where(Tag.organization_id == org_id, Tag.group == "source", func.lower(Tag.name) == name.lower()))
    if tag is None:
        tag = Tag(organization_id=org_id, group="source", name=name)
        db.add(tag)
        db.flush()
    return tag
