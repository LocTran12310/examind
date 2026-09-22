import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import OrgScope
from app.routers.presenters import parsed_many
from app.deps import staff_scope
from app.schemas.exams import BlueprintIn, ExamIn, ExamOut, ExamPatch, ExamQuestionOut, IdsIn, PointsIn
from app.schemas.common import Page
from app.services import exams
from app.services.paging import ListParams, list_params

router = APIRouter(prefix="/exams", tags=["exams"])


def exam_out(db: Session, exam, with_questions: bool = True) -> ExamOut:
    rows = exams.exam_questions(db, exam)
    qs = []
    if with_questions:
        parsed = parsed_many(db, [q for _, q in rows])
        qs = [ExamQuestionOut(**p.model_dump(), position=eq.position, section=eq.section, points=eq.points, row=eq.row) for p, (eq, _) in zip(parsed, rows)]
    return ExamOut(id=exam.id, title=exam.title, subject_id=exam.subject_id, grade=exam.grade, description=exam.description,
                   settings=exam.settings or {}, blueprint=exam.blueprint or [], source=exam.source, question_count=len(rows),
                   total_points=round(sum(eq.points for eq, _ in rows), 4), created_at=exam.created_at, questions=qs)


@router.get("", response_model=Page[ExamOut])
def list_exams(params: ListParams = Depends(list_params), scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    """Column filters: title (text) · grade (number) · source (exact) · subject_id · created_at (date)."""
    rows, total = exams.list_exams(db, scope, params)
    items = [ExamOut(id=e.id, title=e.title, subject_id=e.subject_id, grade=e.grade, description=e.description, settings=e.settings or {},
                     blueprint=e.blueprint or [], source=e.source, question_count=n, total_points=round(p, 4), created_at=e.created_at)
             for e, n, p in rows]
    return Page(items=items, total=total, page=params.page, page_size=params.page_size)


@router.post("", response_model=ExamOut, status_code=201)
def create_exam(body: ExamIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    e = exams.create(db, scope, body.title, body.subject_id, body.grade, body.description, body.settings)
    db.refresh(e)
    return exam_out(db, e)


@router.get("/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    return exam_out(db, exams.get(db, scope, exam_id))


@router.get("/{exam_id}/questions", response_model=Page[ExamQuestionOut])
def exam_question_page(exam_id: uuid.UUID, params: ListParams = Depends(list_params), scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    """Column filters: stem (text) · type · section (exact) · position/points (number)."""
    rows, total = exams.question_page(db, scope, exam_id, params)
    parsed = parsed_many(db, [q for _, q in rows])
    items = [ExamQuestionOut(**p.model_dump(), position=eq.position, section=eq.section, points=eq.points, row=eq.row) for p, (eq, _) in zip(parsed, rows)]
    return Page(items=items, total=total, page=params.page, page_size=params.page_size)


@router.patch("/{exam_id}", response_model=ExamOut)
def patch_exam(exam_id: uuid.UUID, body: ExamPatch, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    e = exams.update(db, scope, exam_id, **body.model_dump(exclude_unset=True))
    db.flush()
    return exam_out(db, e)


@router.delete("/{exam_id}", status_code=204)
def delete_exam(exam_id: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    exams.delete_exam(db, scope, exam_id)
    return Response(status_code=204)


@router.post("/{exam_id}/blueprint")
def blueprint(exam_id: uuid.UUID, body: BlueprintIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    r = exams.apply_blueprint(db, scope, exam_id, body.rows, body.seed, body.replace)
    return {**r, "exam": exam_out(db, exams.get(db, scope, exam_id))}


@router.post("/{exam_id}/questions", response_model=ExamOut)
def add_questions(exam_id: uuid.UUID, body: IdsIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    exams.add_questions(db, scope, exam_id, body.question_ids)
    return exam_out(db, exams.get(db, scope, exam_id))


@router.delete("/{exam_id}/questions/{qid}", response_model=ExamOut)
def remove_question(exam_id: uuid.UUID, qid: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    exams.remove_question(db, scope, exam_id, qid)
    return exam_out(db, exams.get(db, scope, exam_id))


@router.put("/{exam_id}/order", response_model=ExamOut)
def reorder(exam_id: uuid.UUID, body: IdsIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    exams.reorder(db, scope, exam_id, body.question_ids)
    return exam_out(db, exams.get(db, scope, exam_id))


@router.post("/{exam_id}/questions/{qid}/swap", response_model=ExamOut)
def swap(exam_id: uuid.UUID, qid: uuid.UUID, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    exams.swap(db, scope, exam_id, qid)
    return exam_out(db, exams.get(db, scope, exam_id))


@router.patch("/{exam_id}/questions/{qid}", response_model=ExamOut)
def set_points(exam_id: uuid.UUID, qid: uuid.UUID, body: PointsIn, scope: OrgScope = Depends(staff_scope), db: Session = Depends(get_db)):
    exams.set_points(db, scope, exam_id, qid, body.points)
    db.flush()
    return exam_out(db, exams.get(db, scope, exam_id))
