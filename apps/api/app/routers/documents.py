import json
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import storage
from app.core.db import get_db
from app.core.errors import validation
from app.deps import OrgScope
from app.models import Question, QuestionTag, QuestionTopic, Tag, Topic
from app.routers.users import staff_scope
from app.schemas.common import Page
from app.schemas.documents import DocumentBrief, DocumentCreated, DocumentMetaIn, DuplicateCheckIn, DuplicateOut, DocumentOut, ParsedQuestionOut, ReparseIn, TagRef, TopicRef, document_out
from app.schemas.questions import question_out
from app.services.paging import ListParams, list_params
from app.services import documents

router = APIRouter(prefix="/documents", tags=["documents"])


def _json_field(raw: str | None, name: str) -> dict:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        raise validation("JSON không hợp lệ", name)
    if not isinstance(value, dict):
        raise validation("JSON không hợp lệ", name)
    return value


@router.post("", status_code=201, response_model=DocumentCreated)
async def upload(response: Response, file: UploadFile = File(...), meta: str | None = Form(None), config: str | None = Form(None),
                 on_duplicate: str = Form("skip"), replace_id: uuid.UUID | None = Form(None),
                 scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    """`on_duplicate`: skip (same content → the existing document) · replace (+ `replace_id` for a same-name file) · keep_both."""
    data = await file.read()
    doc, action = documents.create_document(db, scope, file.filename or "file", data, _json_field(meta, "meta"), _json_field(config, "config"),
                                            on_duplicate, replace_id)
    if action != "created":
        response.status_code = 200
    return DocumentCreated(document=document_out(doc), duplicate=action != "created", action=action)


@router.post("/check", response_model=list[DuplicateOut])
def check_duplicates(body: DuplicateCheckIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    """Before uploading: which files are already here (same content) or share a name with a document."""
    brief = lambda d: DocumentBrief(id=d.id, filename=d.filename, status=d.status, question_count=d.question_count, created_at=d.created_at)  # noqa: E731
    return [DuplicateOut(name=r["name"], same_file=brief(r["same_file"]) if r["same_file"] else None, same_name=[brief(d) for d in r["same_name"]])
            for r in documents.find_duplicates(db, scope, [f.model_dump() for f in body.files])]


@router.get("", response_model=Page[DocumentOut])
def list_documents(params: ListParams = Depends(list_params), scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    """Column filters: filename, source_name (text) · status, mime (exact) · question_count (number) · created_at (date)."""
    items, total = documents.list_documents(db, scope, params)
    return Page(items=[document_out(d) for d in items], total=total, page=params.page, page_size=params.page_size)


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return document_out(documents.get_document(db, scope, doc_id))


@router.get("/{doc_id}/questions", response_model=list[ParsedQuestionOut])
def document_questions(doc_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    doc = documents.get_document(db, scope, doc_id)
    qs = db.scalars(select(Question).where(Question.source_document_id == doc.id).order_by(Question.part.nulls_first(), Question.number)).all()
    return parsed_many(db, qs)


def question_links(db: Session, qids: list) -> list[tuple[list[TopicRef], list[TagRef]]]:
    topics: dict = {qid: [] for qid in qids}
    tags: dict = {qid: [] for qid in qids}
    if qids:
        for qt, t in db.execute(select(QuestionTopic, Topic).join(Topic, Topic.id == QuestionTopic.topic_id).where(QuestionTopic.question_id.in_(qids))):
            topics[qt.question_id].append(TopicRef(id=t.id, name=t.name, is_primary=qt.is_primary, source=qt.source, score=qt.score))
        for qt, t in db.execute(select(QuestionTag, Tag).join(Tag, Tag.id == QuestionTag.tag_id).where(QuestionTag.question_id.in_(qids))):
            tags[qt.question_id].append(TagRef(id=t.id, group=t.group, name=t.name))
    return [(sorted(topics[q], key=lambda r: not r.is_primary), tags[q]) for q in qids]


def parsed_out(q: Question, topics=(), tags=(), group: str | None = None) -> ParsedQuestionOut:
    base = question_out(q).model_dump()
    return ParsedQuestionOut(**base, number=q.number, part=q.part, confidence=q.confidence, issues=q.issues or [],
                             parse_method=q.parse_method, parse_model=q.parse_model, answer_source=q.answer_source,
                             subject_id=q.subject_id, semester_code=q.semester_code, exam_kind=q.exam_kind,
                             topics=list(topics), tags=list(tags), page=q.page, spot_check=q.spot_check,
                             duplicate_of=q.duplicate_of, source_document_id=q.source_document_id, group=group,
                             flag_evidence=q.flag_evidence)


def parsed_many(db: Session, qs: list[Question], groups: dict | None = None) -> list[ParsedQuestionOut]:
    links = question_links(db, [q.id for q in qs])
    return [parsed_out(q, t, g, (groups or {}).get(q.id)) for q, (t, g) in zip(qs, links)]


@router.get("/{doc_id}/file")
def download(doc_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    doc = documents.get_document(db, scope, doc_id)
    data, _ = storage.get(doc.storage_key)
    from urllib.parse import quote

    return Response(content=data, media_type=doc.mime, headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(doc.filename)}",
        "X-Content-Type-Options": "nosniff",
    })


@router.patch("/{doc_id}", response_model=DocumentOut)
def update_document(doc_id: uuid.UUID, body: DocumentMetaIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return document_out(documents.update_meta(db, scope, doc_id, body.meta))


class ExamFromDocumentIn(BaseModel):
    title: str | None = None


@router.post("/{doc_id}/exam", status_code=201)
def exam_from_document(doc_id: uuid.UUID, body: ExamFromDocumentIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    from app.services import exams

    return exams.from_document(db, scope, doc_id, body.title)


@router.post("/{doc_id}/reparse", response_model=DocumentOut, status_code=202)
def reparse(doc_id: uuid.UUID, body: ReparseIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return document_out(documents.reparse(db, scope, doc_id, body.config))


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    documents.delete_document(db, scope, doc_id)
    return Response(status_code=204)


@router.get("/{doc_id}/pages/{page}.png")
def page_image(doc_id: uuid.UUID, page: int, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    """Source page for the review queue: PDFs rendered once and cached in object storage; images served as-is."""
    doc = documents.get_document(db, scope, doc_id)
    if doc.mime.startswith("image/") and page == 1:
        data, mime = storage.get(doc.storage_key)
        return Response(content=data, media_type=mime, headers={"Cache-Control": "private, max-age=86400"})
    if doc.mime != "application/pdf" or page < 1 or (doc.page_count and page > doc.page_count):
        from app.core.errors import not_found

        raise not_found("Không có ảnh trang")
    key = f"{doc.storage_key.rsplit('/', 1)[0]}/pages/{page}.png"
    try:
        data, _ = storage.get(key)
    except Exception:
        import io

        import pypdfium2 as pdfium

        raw, _ = storage.get(doc.storage_key)
        pdf = pdfium.PdfDocument(raw)
        try:
            img = pdf[page - 1].render(scale=1.5).to_pil()
        finally:
            pdf.close()
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG", optimize=True)
        data = buf.getvalue()
        storage.put(key, data, "image/png")
    return Response(content=data, media_type="image/png", headers={"Cache-Control": "private, max-age=86400, immutable"})
