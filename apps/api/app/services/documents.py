"""Uploaded exam files: validation, dedupe, storage, listing, re-parse (US-01, A-07, A-08, A-14)."""
import hashlib
import re
import unicodedata
import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core import storage
from app.core.errors import AppError, not_found, validation
from app.core.images import sniff
from app.deps import OrgScope
from app.models import Question, Semester, SourceDocument, Subject
from app.services.paging import Col, ListParams, paginate
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


ON_DUPLICATE = ("skip", "replace", "keep_both")


def _norm_name(name: str) -> str:
    """Same name regardless of Unicode form (macOS gives NFD) and case."""
    return unicodedata.normalize("NFC", name or "").strip().casefold()


def find_duplicates(db: Session, scope: OrgScope, files: list[dict]) -> list[dict]:
    """For each {name, sha256}: the document with the same content, and documents with the same name."""
    docs = db.scalars(select(SourceDocument).where(SourceDocument.organization_id == scope.org_id)).all()
    by_hash = {d.file_hash: d for d in docs}
    by_name: dict[str, list[SourceDocument]] = {}
    for d in docs:
        by_name.setdefault(_norm_name(d.filename), []).append(d)
    out = []
    for f in files:
        same = by_hash.get(str(f.get("sha256") or "").lower())
        names = [d for d in by_name.get(_norm_name(f.get("name", "")), []) if d is not same]
        out.append({"name": f.get("name"), "same_file": same, "same_name": sorted(names, key=lambda d: d.created_at, reverse=True)})
    return out


def create_document(db: Session, scope: OrgScope, filename: str, data: bytes, meta: dict, config: dict,
                    on_duplicate: str = "skip", replace_id=None) -> tuple[SourceDocument, str]:
    """Returns (document, action) with action created | skipped | reparsed | replaced.

    The same content is never stored twice: `skip` returns the existing document, `replace` re-parses it.
    A different file with the name of an existing one is added (`keep_both`, `skip` when no target) or
    replaces the chosen document's file (`replace` + `replace_id`), keeping approved and exam questions.
    """
    if on_duplicate not in ON_DUPLICATE:
        raise validation("Cách xử lý file trùng không hợp lệ", "on_duplicate")
    if not data:
        raise validation("File rỗng", "file")
    if len(data) > MAX_BYTES:
        raise AppError("file_too_large", "File tối đa 30MB", 422, {"file": "File tối đa 30MB"})
    kind, mime = detect_kind(filename, data)
    digest = hashlib.sha256(data).hexdigest()
    from app.services.ingestion_settings import resolve_config

    existing = db.scalar(select(SourceDocument).where(SourceDocument.organization_id == scope.org_id, SourceDocument.file_hash == digest))
    if existing:
        if on_duplicate == "replace":
            reparse(db, scope, existing.id, config or None)
            if meta:
                update_meta(db, scope, existing.id, {**{k: v for k, v in (existing.meta or {}).items() if k != "detected"}, **meta})
            return existing, "reparsed"
        return existing, "skipped"
    if on_duplicate == "replace" and replace_id:
        target = get_document(db, scope, replace_id)
        if target.status in ("queued", "processing"):
            raise AppError("busy", "Tài liệu đang được xử lý", 409)
        old_key = target.storage_key
        key = f"{scope.org_id}/documents/{target.id}/{uuid.uuid4().hex[:8]}-{_safe_name(filename)}"
        storage.put(key, data, mime)
        target.filename, target.mime, target.size, target.file_hash, target.storage_key = (filename or "file")[:300], mime, len(data), digest, key
        if meta:
            target.meta = {**(target.meta or {}), **clean_meta(db, scope, meta)}
        if config:
            target.processing_config = resolve_config(db, scope, config)
        target.status, target.error, target.page_count = "queued", None, None
        db.flush()
        queue.enqueue(db, "ingest_document", {"document_id": str(target.id)})
        audit.record(db, scope.user, scope.org_id, "document.replace", "document", target.id, filename=target.filename, kind=kind)
        try:
            storage.client().delete_object(Bucket=storage.get_settings().s3_bucket, Key=old_key)
        except Exception:  # the old file is only garbage now; cleanup is best effort
            pass
        return target, "replaced"

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
    return doc, "created"


def get_document(db: Session, scope: OrgScope, doc_id) -> SourceDocument:
    doc = db.get(SourceDocument, doc_id)
    if doc is None or doc.organization_id != scope.org_id:
        raise not_found("Không tìm thấy tài liệu")
    return doc


DOCUMENT_COLS = {
    "filename": Col(SourceDocument.filename),
    "source_name": Col(SourceDocument.meta["source_name"].astext),
    "status": Col(SourceDocument.status, "exact"),
    "mime": Col(SourceDocument.mime, "exact"),
    "question_count": Col(SourceDocument.question_count, "number"),
    "created_at": Col(SourceDocument.created_at, "date"),
}


def list_documents(db: Session, scope: OrgScope, params: ListParams):
    stmt = select(SourceDocument).where(SourceDocument.organization_id == scope.org_id)
    return paginate(db, stmt, params, DOCUMENT_COLS, search=[SourceDocument.filename, SourceDocument.meta["source_name"].astext],
                    default_sort=[SourceDocument.created_at.desc(), SourceDocument.id])


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


QUESTION_META = ("subject_id", "grade", "semester_code", "exam_kind")


def update_meta(db: Session, scope: OrgScope, doc_id, meta: dict) -> SourceDocument:
    """Edit subject / grade / đợt / năm học / nguồn after upload (e.g. confirm the detected header);
    the document's questions follow, including the source tag."""
    from app.ingestion.pipeline import _source_tag
    from app.models import QuestionTag

    doc = get_document(db, scope, doc_id)
    old = dict(doc.meta or {})
    new = clean_meta(db, scope, meta)
    if old.get("detected"):
        new["detected"] = old["detected"]
    doc.meta = new
    changes = {k: new.get(k) for k in QUESTION_META if new.get(k) != old.get(k)}
    questions = list(db.scalars(select(Question).where(Question.source_document_id == doc.id)))
    for q in questions:
        for k, v in changes.items():
            setattr(q, k, uuid.UUID(v) if k == "subject_id" and v else v)
    if new.get("source_name") != old.get("source_name"):
        old_tag = _source_tag(db, doc.organization_id, old.get("source_name"))
        new_tag = _source_tag(db, doc.organization_id, new.get("source_name"))
        ids = [q.id for q in questions]
        if old_tag and ids:
            db.execute(delete(QuestionTag).where(QuestionTag.tag_id == old_tag.id, QuestionTag.question_id.in_(ids)))
        if new_tag:
            for qid in ids:
                db.add(QuestionTag(question_id=qid, tag_id=new_tag.id))
    db.flush()
    audit.record(db, scope.user, scope.org_id, "document.meta", "document", doc.id,
                 changes={k: v for k, v in new.items() if k != "detected" and v != old.get(k)})
    return doc


def delete_document(db: Session, scope: OrgScope, doc_id) -> None:
    doc = get_document(db, scope, doc_id)
    from app.services.bank import release_duplicates_of

    gone = (Question.source_document_id == doc.id, Question.status.notin_(KEEP_ON_REPARSE))
    release_duplicates_of(db, select(Question.id).where(*gone))
    db.execute(delete(Question).where(*gone))
    try:
        storage.client().delete_object(Bucket=storage.get_settings().s3_bucket, Key=doc.storage_key)
    except Exception:  # object storage cleanup is best effort
        pass
    audit.record(db, scope.user, scope.org_id, "document.delete", "document", doc.id, filename=doc.filename)
    db.delete(doc)
