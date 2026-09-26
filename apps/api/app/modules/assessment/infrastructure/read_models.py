"""Search and report reads of assessment (SQLAlchemy Core over its tables; class names and people are read from the
academic and identity tables, ADR-01)."""
import uuid

from sqlalchemy import Integer, func, select
from sqlalchemy.orm import Session

from app.modules.assessment.application.dto import (
    AssignmentRow,
    AttemptRow,
    ExamQuestionRow,
    ExamSummary,
    Person,
    PersonalReviewRow,
    PracticeAttemptRow,
)
from app.modules.assessment.domain.entities import Assignment, Attempt, AttemptAnswer, Exam
from app.modules.assessment.domain.services.scoring import scaled
from app.modules.assessment.infrastructure import orm  # noqa: F401  (mapping)
from app.shared.application.search import Page, SearchRequest
from app.shared.infrastructure.schema.academic import classes
from app.shared.infrastructure.schema.assessment import assignment_targets, assignments, attempt_answers, attempts, exam_questions, exams
from app.shared.infrastructure.schema.bank import questions
from app.shared.infrastructure.schema.identity import users
from app.shared.infrastructure.sql_search import Col, contains, search, where_clauses

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
def _scoped(stmt, subject_id: uuid.UUID | str | None):
    """"none" is the exams nobody gave a subject — a real answer, not a missing filter."""
    if subject_id == "none":
        return stmt.where(e_c.subject_id.is_(None))
    return stmt.where(e_c.subject_id == subject_id) if subject_id else stmt


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

    def search(self, org_id: uuid.UUID, req: SearchRequest, subject_id: uuid.UUID | str | None = None) -> Page[ExamSummary]:
        stmt = (select(Exam, _COUNTS.c.n, _COUNTS.c.pts).outerjoin(_COUNTS, _COUNTS.c.exam_id == e_c.id)
                .where(e_c.organization_id == org_id, e_c.source != "adaptive"))
        stmt = _scoped(stmt, subject_id)
        rows, total = search(self.session, stmt, req, EXAM_COLS, text=[e_c.title], default_sort=[e_c.created_at.desc(), e_c.id],
                             scalars=False)
        return Page([ExamSummary(e, n or 0, round(float(p or 0), 4)) for e, n, p in rows], total, req.page, req.limit)

    def subject_counts(self, org_id: uuid.UUID, req: SearchRequest) -> dict[str, int]:
        """Exams per subject under the rest of the search — the numbers on the subject tabs.

        The subject scope itself is left out on purpose: a tab has to say what it would show if you clicked it,
        and counting inside the tab already chosen would make every other tab read 0."""
        stmt = select(e_c.subject_id, func.count()).select_from(exams).where(e_c.organization_id == org_id, e_c.source != "adaptive")
        if req.q:
            stmt = stmt.where(contains(e_c.title, req.q))
        for c in where_clauses(EXAM_COLS, req.filters):
            stmt = stmt.where(c)
        rows = self.session.execute(stmt.group_by(e_c.subject_id)).all()
        return {("none" if k is None else str(k)): n for k, n in rows}

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


#: `auto_submitted` is **derived, not stored**: the worker dates an expiry sweep at the deadline plus a grace
#: window, so a sitting whose `submitted_at` is past its own deadline was closed by the system rather than by the
#: student. Nothing in the schema records that, and if a submit path ever writes a later timestamp for another
#: reason this derivation will be wrong — which is why it lives here with its reasoning and not in a column.
_AUTO = at_c.submitted_at > at_c.deadline_at
#: minutes over the whole sitting; NULL while it is still open (class-overview-and-subjects ADR-02)
_MINUTES = func.round(func.extract("epoch", at_c.submitted_at - at_c.started_at) / 60.0).cast(Integer)

ATTEMPT_COLS = {
    "student_id": Col(at_c.student_id, "uuid"),
    "assignment_id": Col(at_c.assignment_id, "uuid"),
    "exam_id": Col(at_c.exam_id, "uuid"),
    "status": Col(at_c.status, "enum", values=("in_progress", "submitted")),
    "started_at": Col(at_c.started_at, "date"),
    "submitted_at": Col(at_c.submitted_at, "date"),
    "score": Col(at_c.score, "number"),
    "exam_title": Col(e_c.title),
}


class SqlAttemptHistoryReader:
    """Every sitting of the organisation, newest first — the list a teacher opens to ask what a student has done.

    Joined to exams and users so a row reads without a second request, and to assignments only for its title: a
    practice sitting has no assignment and must still appear (that is most of what `/me/practice` shows).
    """

    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID, req: SearchRequest) -> Page[AttemptRow]:
        stmt = (select(at_c.id, e_c.title, a_c.title.label("assignment_title"), at_c.started_at, at_c.submitted_at,
                       _MINUTES.label("minutes"), at_c.score, at_c.max_score, at_c.status, _AUTO.label("auto"),
                       at_c.student_id, users.c.full_name, users.c.username)
                .select_from(attempts)
                .join(exams, exams.c.id == at_c.exam_id)
                .join(users, users.c.id == at_c.student_id)
                .outerjoin(assignments, assignments.c.id == at_c.assignment_id)
                .where(at_c.organization_id == org_id))
        rows, total = search(self.session, stmt, req, ATTEMPT_COLS, text=[e_c.title],
                             default_sort=[at_c.started_at.desc(), at_c.id], scalars=False)
        return Page([AttemptRow(
            attempt_id=r.id, exam_title=r.title, assignment_title=r.assignment_title, started_at=r.started_at,
            submitted_at=r.submitted_at, minutes=r.minutes, score=r.score, max_score=r.max_score or 0.0,
            score10=scaled(r.score, r.max_score) if r.score is not None else None,
            status=r.status, auto_submitted=bool(r.auto), student_id=r.student_id,
            student_name=r.full_name, username=r.username) for r in rows], total, req.page, req.limit)


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

    def practice_attempts(self, org_id: uuid.UUID, student_id: uuid.UUID, limit: int) -> list[PracticeAttemptRow]:
        # a student may belong to several organisations: only this one's practice
        rows = self.session.execute(select(Attempt, Exam).join(Exam, e_c.id == at_c.exam_id)
                                    .where(at_c.student_id == student_id, at_c.assignment_id.is_(None), e_c.organization_id == org_id)
                                    .order_by(at_c.started_at.desc()).limit(limit)).all()
        return [PracticeAttemptRow(a.id, e.title, a.status, a.started_at, a.submitted_at,
                                   scaled(a.score or 0, a.max_score or 0) if a.status == "submitted" else None,
                                   dict(e.settings or {}), e.subject_id)
                for a, e in rows]

    def latest_review(self, org_id: uuid.UUID, student_id: uuid.UUID) -> PersonalReviewRow | None:
        """The newest personal review paper of one student, with how many that student has in all.

        The count is a window function on the same statement, not a second query and not `len(rows)`: the
        window is computed over the whole result set *before* LIMIT, so it still says 3 when the row returned
        is only the latest of three. Counting in Python after `limit(1)` would answer 1 every time (ADR-02)."""
        t_c = assignment_targets.c
        row = self.session.execute(
            select(Assignment, at_c.status, func.count().over().label("total")).join(Exam, e_c.id == a_c.exam_id)
            .join(assignment_targets, t_c.assignment_id == a_c.id)
            .outerjoin(attempts, (at_c.assignment_id == a_c.id) & (at_c.student_id == student_id))
            .where(t_c.user_id == student_id, e_c.source == "adaptive", a_c.organization_id == org_id).order_by(a_c.created_at.desc()).limit(1)).first()
        return PersonalReviewRow(row[0].id, row[0].title, row[1] or "not_started", row[0].open_at, row[0].close_at, row[2]) if row else None
