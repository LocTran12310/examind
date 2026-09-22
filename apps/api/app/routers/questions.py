import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import not_found
from app.deps import OrgScope, org_scope
from app.models import Question
from app.schemas.questions import QuestionOut, QuestionPatch, question_out

router = APIRouter(prefix="/questions", tags=["questions"])


def _staff(scope: OrgScope):
    from app.core.errors import forbidden

    if scope.role not in ("org_admin", "teacher"):
        raise forbidden()
    return scope



def _uuid_list(raw: str | None) -> list[uuid.UUID]:
    """`a,b,c` → UUIDs (comma list keeps the URL state a single param)."""
    from app.core.errors import validation

    try:
        return [uuid.UUID(x) for x in (raw or "").split(",") if x.strip()]
    except ValueError:
        raise validation("Chuyên đề không hợp lệ", "topic_ids")


def _filters(q: str = "", subject_id: str | None = None, grade: int | None = None, semester_code: str | None = None,
             exam_kind: str | None = None, type: str | None = None, difficulty: str | None = None, status: str = "usable",
             topic_id: uuid.UUID | None = None, topic_ids: str | None = None, tag_ids: list[str] = Query(default=[]),
             document_id: uuid.UUID | None = None, school_year: str | None = None) -> dict:
    """The bank's filter params; `tag_ids` may repeat or be a comma list, `subject_id` may be "none"."""
    from app.core.errors import validation

    if subject_id and subject_id != "none":
        try:
            subject_id = uuid.UUID(subject_id)
        except ValueError:
            raise validation("Môn học không hợp lệ", "subject_id")
    try:
        tags = [uuid.UUID(x) for raw in tag_ids for x in raw.split(",") if x.strip()]
    except ValueError:
        raise validation("Tag không hợp lệ", "tag_ids")
    return dict(q=q, subject_id=subject_id or None, grade=grade, semester_code=semester_code, exam_kind=exam_kind, type=type,
                difficulty=difficulty, status=status, topic_id=topic_id, topic_ids=_uuid_list(topic_ids), tag_ids=tags,
                document_id=document_id, school_year=school_year or None)


@router.get("")
def list_questions(filters: dict = Depends(_filters), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                   scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    from app.routers.documents import parsed_many
    from app.services import bank

    _staff(scope)
    items, total = bank.search(db, scope, page=page, page_size=page_size, **filters)
    return {"items": parsed_many(db, items), "total": total, "page": page, "page_size": page_size}


@router.get("/facets")
def question_facets(filters: dict = Depends(_filters), scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    """Counts per subject / topic (subtree) / type / difficulty / grade / đợt / năm học / tag for the filter sheet."""
    from app.services import bank

    _staff(scope)
    return bank.facets(db, scope, **filters)


@router.post("", status_code=201)
def create_question(body: dict, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    from app.routers.documents import parsed_many
    from app.services import bank

    _staff(scope)
    return parsed_many(db, [bank.create(db, scope, body)])[0]


@router.post("/bulk")
def bulk_questions(body: dict, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    from app.services import bank

    _staff(scope)
    return {"updated": bank.bulk(db, scope, body.get("ids") or [], body.get("set") or {})}


@router.delete("/{question_id}", status_code=204)
def delete_question(question_id: uuid.UUID, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    from fastapi import Response

    from app.services import bank

    _staff(scope)
    bank.delete(db, scope, question_id)
    return Response(status_code=204)


def _get(db: Session, scope: OrgScope, qid) -> Question:
    q = db.get(Question, qid)
    if q is None or q.organization_id != scope.org_id:
        raise not_found("Không tìm thấy câu hỏi")
    return q


@router.get("/demo", response_model=QuestionOut)
def demo(scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    q = db.scalar(select(Question).where(Question.organization_id == scope.org_id, Question.source == "demo").limit(1))
    if q is None:
        raise not_found("Chưa có câu hỏi mẫu")
    return question_out(q)


@router.get("/{question_id}")
def get_question(question_id: uuid.UUID, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    q = _get(db, scope, question_id)
    if scope.role == "student":
        # students never receive answers/solutions from this endpoint; exams expose them after submission
        return question_out(q, hide_answer=True)
    from app.routers.documents import parsed_many

    return parsed_many(db, [q])[0]


@router.patch("/{question_id}")
def patch_question(question_id: uuid.UUID, body: QuestionPatch, scope: OrgScope = Depends(org_scope), db: Session = Depends(get_db)):
    from app.core.errors import forbidden
    from app.routers.documents import parsed_many
    from app.services import review

    if scope.role not in ("org_admin", "teacher"):
        raise forbidden()
    q = review.edit(db, scope, question_id, body.model_dump(exclude_unset=True))
    return parsed_many(db, [q])[0]
