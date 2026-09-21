"""Uploaded exam files: validation, dedupe, storage, listing, re-parse (US-01, A-07, A-08, A-14)."""
import hashlib
import re
import uuid

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.core import storage
from app.core.errors import AppError, not_found, validation
from app.core.images import sniff
from app.deps import OrgScope
from app.models import Question, Semester, SourceDocument, Subject
from app.services import audit
from app.worker import queue

MAX_BYTES = 30 * 1024 * 1024
EXAM_KINDS = ("Giữa kỳ", "Cuối kỳ", "Khảo sát", "Thi thử", "Ôn tập", "Khác")
KEEP_ON_REPARSE = ("approved",)
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def detect_kind(filename: str, data: bytes) -> tuple[str, str]:
    """Return (kind, mime) from magic bytes, checked against the extension."""
    name = (filename or "").lower()
    if data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        raise AppError("unsupported_file", "File .doc (Word 97–2003) chưa được hỗ trợ — hãy lưu lại dưới dạng .docx", 422, {"file": "Lưu lại dưới dạng .docx"})
    if data[:4] == b"PK\x03\x04" and name.endswith(".docx"):
        return "docx", DOCX
    if data[:5] == b"%PDF-":
        return "pdf", "application/pdf"
    mime, _, _ = sniff(data)
    if mime in ("image/png", "image/jpeg"):
        return "image", mime
    raise AppError("unsupported_file", "Chỉ hỗ trợ .docx, .pdf, .png, .jpg", 422, {"file": "Chỉ hỗ trợ .docx, .pdf, .png, .jpg"})


def clean_meta(db: Session, scope: OrgScope, meta: dict) -> dict:
    out: dict = {}
    if meta.get("subject_id"):
        subject = db.get(Subject, uuid.UUID(str(meta["subject_id"])))
        if subject is None or subject.organization_id != scope.org_id:
            raise validation("Môn học không hợp lệ", "subject_id")
        out["subject_id"] = str(subject.id)
    if meta.get("grade") not in (None, ""):
        grade = int(meta["grade"])
        if not 1 <= grade <= 12:
            raise validation("Khối lớp từ 1 đến 12", "grade")
        out["grade"] = grade
    if meta.get("semester_code"):
        codes = set(db.scalars(select(Semester.code).where(Semester.organization_id == scope.org_id)))
        if meta["semester_code"] not in codes:
            raise validation("Học kỳ không hợp lệ", "semester_code")
        out["semester_code"] = meta["semester_code"]
    if meta.get("exam_kind"):
        if meta["exam_kind"] not in EXAM_KINDS:
            raise validation("Loại đề không hợp lệ", "exam_kind")
        out["exam_kind"] = meta["exam_kind"]
    if meta.get("school_year"):
        if not re.fullmatch(r"\d{4}-\d{4}", str(meta["school_year"])):
            raise validation("Năm học dạng 2026-2027", "school_year")
        out["school_year"] = meta["school_year"]
    if meta.get("source_name"):
        out["source_name"] = str(meta["source_name"]).strip()[:100]
    return out


def _safe_name(filename: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", filename or "file")[-120:]
    return base or "file"


def create_document(db: Session, scope: OrgScope, filename: str, data: bytes, meta: dict, config: dict) -> tuple[SourceDocument, bool]:
    if not data:
        raise validation("File rỗng", "file")
    if len(data) > MAX_BYTES:
        raise AppError("file_too_large", "File tối đa 30MB", 422, {"file": "File tối đa 30MB"})
    kind, mime = detect_kind(filename, data)
    digest = hashlib.sha256(data).hexdigest()
    existing = db.scalar(select(SourceDocument).where(SourceDocument.organization_id == scope.org_id, SourceDocument.file_hash == digest))
    if existing:
        return existing, True
    from app.services.ingestion_settings import resolve_config

    doc_id = uuid.uuid4()
    key = f"{scope.org_id}/documents/{doc_id}/{_safe_name(filename)}"
    storage.put(key, data, mime)
    doc = SourceDocument(id=doc_id, organization_id=scope.org_id, filename=(filename or "file")[:300], mime=mime, size=len(data),
                         file_hash=digest, storage_key=key, status="queued", meta=clean_meta(db, scope, meta),
                         processing_config=resolve_config(db, scope, config), uploaded_by=scope.user.id, log=[])
    db.add(doc)
    db.flush()
    queue.enqueue(db, "ingest_document", {"document_id": str(doc.id)})
    audit.record(db, scope.user, scope.org_id, "document.upload", "document", doc.id, filename=doc.filename, kind=kind)
    return doc, False


def get_document(db: Session, scope: OrgScope, doc_id) -> SourceDocument:
    doc = db.get(SourceDocument, doc_id)
    if doc is None or doc.organization_id != scope.org_id:
        raise not_found("Không tìm thấy tài liệu")
    return doc


def list_documents(db: Session, scope: OrgScope, q: str = "", status: str | None = None, page: int = 1, page_size: int = 50):
    stmt = select(SourceDocument).where(SourceDocument.organization_id == scope.org_id)
    if status:
        stmt = stmt.where(SourceDocument.status == status)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(SourceDocument.filename.ilike(like), SourceDocument.meta["source_name"].astext.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(SourceDocument.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return items, total


def reparse(db: Session, scope: OrgScope, doc_id, config: dict | None) -> SourceDocument:
    from app.services.ingestion_settings import resolve_config

    doc = get_document(db, scope, doc_id)
    if doc.status in ("queued", "processing"):
        raise AppError("busy", "Tài liệu đang được xử lý", 409)
    if config is not None:
        doc.processing_config = resolve_config(db, scope, config)
    doc.status, doc.error = "queued", None
    queue.enqueue(db, "ingest_document", {"document_id": str(doc.id)})
    audit.record(db, scope.user, scope.org_id, "document.reparse", "document", doc.id)
    return doc


def delete_document(db: Session, scope: OrgScope, doc_id) -> None:
    doc = get_document(db, scope, doc_id)
    db.execute(delete(Question).where(Question.source_document_id == doc.id, Question.status.notin_(KEEP_ON_REPARSE)))
    try:
        storage.client().delete_object(Bucket=storage.get_settings().s3_bucket, Key=doc.storage_key)
    except Exception:  # object storage cleanup is best effort
        pass
    audit.record(db, scope.user, scope.org_id, "document.delete", "document", doc.id, filename=doc.filename)
    db.delete(doc)
