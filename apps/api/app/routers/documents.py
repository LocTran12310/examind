import json
import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import storage
from app.core.db import get_db
from app.core.errors import validation
from app.deps import OrgScope
from app.models import Question, QuestionTag, QuestionTopic, Tag, Topic
from app.routers.users import staff_scope
from app.schemas.common import Page
from app.schemas.documents import DocumentCreated, DocumentOut, ParsedQuestionOut, ReparseIn, TagRef, TopicRef, document_out
from app.schemas.questions import question_out
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
                 scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    data = await file.read()
    doc, duplicate = documents.create_document(db, scope, file.filename or "file", data, _json_field(meta, "meta"), _json_field(config, "config"))
    if duplicate:
        response.status_code = 200
    return DocumentCreated(document=document_out(doc), duplicate=duplicate)


@router.get("", response_model=Page[DocumentOut])
def list_documents(q: str = "", status: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
                   scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    items, total = documents.list_documents(db, scope, q, status, page, page_size)
    return Page(items=[document_out(d) for d in items], total=total, page=page, page_size=page_size)


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return document_out(documents.get_document(db, scope, doc_id))


@router.get("/{doc_id}/questions", response_model=list[ParsedQuestionOut])
def document_questions(doc_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    doc = documents.get_document(db, scope, doc_id)
    qs = db.scalars(select(Question).where(Question.source_document_id == doc.id).order_by(Question.part.nulls_first(), Question.number)).all()
    return [parsed_out(q, *links) for q, links in zip(qs, question_links(db, [q.id for q in qs]))]


def question_links(db: Session, qids: list) -> list[tuple[list[TopicRef], list[TagRef]]]:
    topics: dict = {qid: [] for qid in qids}
    tags: dict = {qid: [] for qid in qids}
    if qids:
        for qt, t in db.execute(select(QuestionTopic, Topic).join(Topic, Topic.id == QuestionTopic.topic_id).where(QuestionTopic.question_id.in_(qids))):
            topics[qt.question_id].append(TopicRef(id=t.id, name=t.name, is_primary=qt.is_primary, source=qt.source, score=qt.score))
        for qt, t in db.execute(select(QuestionTag, Tag).join(Tag, Tag.id == QuestionTag.tag_id).where(QuestionTag.question_id.in_(qids))):
            tags[qt.question_id].append(TagRef(id=t.id, group=t.group, name=t.name))
    return [(sorted(topics[q], key=lambda r: not r.is_primary), tags[q]) for q in qids]


def parsed_out(q: Question, topics=(), tags=()) -> ParsedQuestionOut:
    base = question_out(q).model_dump()
    return ParsedQuestionOut(**base, number=q.number, part=q.part, confidence=q.confidence, issues=q.issues or [],
                             parse_method=q.parse_method, parse_model=q.parse_model, answer_source=q.answer_source,
                             subject_id=q.subject_id, semester_code=q.semester_code, exam_kind=q.exam_kind,
                             topics=list(topics), tags=list(tags))


@router.get("/{doc_id}/file")
def download(doc_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    doc = documents.get_document(db, scope, doc_id)
    data, _ = storage.get(doc.storage_key)
    from urllib.parse import quote

    return Response(content=data, media_type=doc.mime, headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(doc.filename)}",
        "X-Content-Type-Options": "nosniff",
    })


@router.post("/{doc_id}/reparse", response_model=DocumentOut, status_code=202)
def reparse(doc_id: uuid.UUID, body: ReparseIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return document_out(documents.reparse(db, scope, doc_id, body.config))


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    documents.delete_document(db, scope, doc_id)
    return Response(status_code=204)
