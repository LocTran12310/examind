"""Search and report reads of assessment (SQLAlchemy Core over its tables; class names and people are read from the
academic and identity tables, ADR-01)."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.assessment.application.dto import (
    AssignmentRow, ExamQuestionRow, ExamSummary, Person, PersonalReviewRow, PracticeAttemptRow,
)
from app.modules.assessment.domain.entities import Assignment, Attempt, AttemptAnswer, Exam
from app.modules.assessment.domain.services.scoring import scaled
from app.modules.assessment.infrastructure import orm  # noqa: F401  (mapping)
from app.shared.application.search import Page, SearchRequest
from app.shared.infrastructure.schema.academic import classes
from app.shared.infrastructure.schema.assessment import assignment_targets, assignments, attempt_answers, attempts, exam_questions, exams
from app.shared.infrastructure.schema.bank import questions
from app.shared.infrastructure.schema.identity import users
from app.shared.infrastructure.sql_search import Col, search

e_c, eq_c, a_c, at_c, q_c = exams.c, exam_questions.c, assignments.c, attempts.c, questions.c

_COUNTS = (select(eq_c.exam_id, func.count().label("n"), func.coalesce(func.sum(eq_c.points), 0).label("pts"))
           .group_by(eq_c.exam_id).subquery())
EXAM_COLS = {
    "title": Col(e_c.title),
    "grade": Col(e_c.grade, "number"),
    "source": Col(e_c.source, "exact"),
    "subject_id": Col(e_c.subject_id, "uuid"),
    "created_at": Col(e_c.created_at, "date"),
    "question_count": Col(func.coalesce(_COUNTS.c.n, 0), filterable=False),
    "total_points": Col(func.coalesce(_COUNTS.c.pts, 0), filterable=False),
}
EXAM_QUESTION_COLS = {
    "position": Col(eq_c.position, "number"),
    "stem": Col(q_c.stem),
    "type": Col(q_c.type, "exact"),
    "section": Col(eq_c.section, "exact"),
    "points": Col(eq_c.points, "number"),
}
ASSIGNMENT_COLS = {
    "title": Col(a_c.title),
    "exam_id": Col(a_c.exam_id, "uuid"),
    "open_at": Col(a_c.open_at, "date"),
    "close_at": Col(a_c.close_at, "date"),
    "duration_minutes": Col(a_c.duration_minutes, "number"),
}


class SqlExamReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID, req: SearchRequest) -> Page[ExamSummary]:
        stmt = (select(Exam, _COUNTS.c.n, _COUNTS.c.pts).outerjoin(_COUNTS, _COUNTS.c.exam_id == e_c.id)
                .where(e_c.organization_id == org_id, e_c.source != "adaptive"))
        rows, total = search(self.session, stmt, req, EXAM_COLS, text=[e_c.title], default_sort=[e_c.created_at.desc(), e_c.id],
                             scalars=False)
        return Page([ExamSummary(e, n or 0, round(float(p or 0), 4)) for e, n, p in rows], total, req.page, req.limit)

    def questions(self, exam_id: uuid.UUID, req: SearchRequest) -> Page[ExamQuestionRow]:
        stmt = (select(eq_c.question_id, eq_c.position, eq_c.section, eq_c.points, eq_c.row)
                .select_from(exam_questions).join(questions, q_c.id == eq_c.question_id).where(eq_c.exam_id == exam_id))
        rows, total = search(self.session, stmt, req, EXAM_QUESTION_COLS, text=[q_c.stem], default_sort=[eq_c.position], scalars=False)
        return Page([ExamQuestionRow(r.question_id, r.position, r.section, r.points, r.row) for r in rows], total, req.page, req.limit)


class SqlAssignmentReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID, req: SearchRequest) -> Page[AssignmentRow]:
        stmt = select(Assignment).where(a_c.organization_id == org_id)
        rows, total = search(self.session, stmt, req, ASSIGNMENT_COLS, text=[a_c.title], default_sort=[a_c.open_at.desc(), a_c.id])
        ids = [a.id for a in rows]
        submitted, names = {}, {}
        if ids:
            submitted = dict(self.session.execute(
                select(at_c.assignment_id, func.count(func.distinct(at_c.student_id)))
                .where(at_c.assignment_id.in_(ids), at_c.status == "submitted").group_by(at_c.assignment_id)).all())
            for aid, name in self.session.execute(
                    select(assignment_targets.c.assignment_id, classes.c.name).select_from(assignment_targets)
                    .join(classes, classes.c.id == assignment_targets.c.class_id).where(assignment_targets.c.assignment_id.in_(ids))):
                names.setdefault(aid, []).append(name)
        return Page([AssignmentRow(a, submitted.get(a.id, 0), names.get(a.id, [])) for a in rows], total, req.page, req.limit)


class SqlResultReader:
    def __init__(self, session: Session):
        self.session = session

    def attempts(self, assignment_id: uuid.UUID) -> list[Attempt]:
        return list(self.session.scalars(select(Attempt).where(at_c.assignment_id == assignment_id).order_by(at_c.started_at)))

    def answers(self, attempt_ids: list[uuid.UUID]) -> list[AttemptAnswer]:
        return list(self.session.scalars(select(AttemptAnswer).where(attempt_answers.c.attempt_id.in_(list(attempt_ids)))))

    def people(self, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, Person]:
        if not user_ids:
            return {}
        rows = self.session.execute(select(users.c.id, users.c.full_name, users.c.username).where(users.c.id.in_(list(user_ids))))
        return {r.id: Person(r.id, r.full_name, r.username) for r in rows}


class SqlPersonalReader:
    def __init__(self, session: Session):
        self.session = session

    def practice_attempts(self, student_id: uuid.UUID, limit: int) -> list[PracticeAttemptRow]:
        rows = self.session.execute(select(Attempt, Exam).join(Exam, e_c.id == at_c.exam_id)
                                    .where(at_c.student_id == student_id, at_c.assignment_id.is_(None))
                                    .order_by(at_c.started_at.desc()).limit(limit)).all()
        return [PracticeAttemptRow(a.id, e.title, a.status, a.started_at, a.submitted_at,
                                   scaled(a.score or 0, a.max_score or 0) if a.status == "submitted" else None, dict(e.settings or {}))
                for a, e in rows]

    def latest_review(self, student_id: uuid.UUID) -> PersonalReviewRow | None:
        t_c = assignment_targets.c
        row = self.session.execute(
            select(Assignment, at_c.status).join(Exam, e_c.id == a_c.exam_id)
            .join(assignment_targets, t_c.assignment_id == a_c.id)
            .outerjoin(attempts, (at_c.assignment_id == a_c.id) & (at_c.student_id == student_id))
            .where(t_c.user_id == student_id, e_c.source == "adaptive").order_by(a_c.created_at.desc()).limit(1)).first()
        return PersonalReviewRow(row[0].id, row[0].title, row[1] or "not_started") if row else None
