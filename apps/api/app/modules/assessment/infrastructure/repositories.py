from datetime import datetime
import uuid

from sqlalchemy import delete, exists, func, or_, select, update
from sqlalchemy.orm import Session

from app.modules.assessment.domain.entities import (
    AnswerFact,
    Assignment,
    AssignmentTarget,
    Attempt,
    AttemptAnswer,
    Exam,
    ExamQuestion,
)
from app.modules.assessment.infrastructure import orm  # noqa: F401  (mapping)
from app.shared.infrastructure.schema.assessment import (
    answer_facts,
    assignment_targets,
    assignments,
    attempt_answers,
    attempts,
    exam_questions,
    exams,
)

eq_c, at_c, t_c, f_c = exam_questions.c, attempts.c, assignment_targets.c, answer_facts.c


class _Repo:
    def __init__(self, session: Session):
        self.session = session

    def flush(self) -> None:
        self.session.flush()


class SqlExamRepository(_Repo):
    def get(self, org_id: uuid.UUID, exam_id: uuid.UUID) -> Exam | None:
        e = self.session.get(Exam, exam_id)
        return e if e is not None and e.organization_id == org_id else None

    def get_any(self, exam_id: uuid.UUID) -> Exam | None:
        return self.session.get(Exam, exam_id)

    def subjects_of(self, exam_ids: list[uuid.UUID]) -> dict[uuid.UUID, uuid.UUID | None]:
        if not exam_ids:
            return {}
        rows = self.session.execute(select(exams.c.id, exams.c.subject_id).where(exams.c.id.in_(set(exam_ids)))).all()
        return {i: s for i, s in rows}

    def add(self, exam: Exam) -> None:
        self.session.add(exam)
        self.session.flush()

    def remove(self, exam: Exam) -> None:
        self.session.delete(exam)
        self.session.flush()

    def questions(self, exam_id: uuid.UUID) -> list[ExamQuestion]:
        self.session.flush()
        return list(self.session.scalars(select(ExamQuestion).where(eq_c.exam_id == exam_id).order_by(eq_c.position)))

    def question(self, exam_id: uuid.UUID, question_id: uuid.UUID) -> ExamQuestion | None:
        return self.session.scalar(select(ExamQuestion).where(eq_c.exam_id == exam_id, eq_c.question_id == question_id))

    def add_question(self, eq: ExamQuestion) -> None:
        self.session.add(eq)

    def remove_question(self, eq: ExamQuestion) -> None:
        self.session.delete(eq)
        self.session.flush()

    def clear(self, exam_id: uuid.UUID) -> None:
        self.session.execute(delete(ExamQuestion).where(ExamQuestion.exam_id == exam_id))
        self.session.flush()

    def has_attempts(self, exam_id: uuid.UUID) -> bool:
        return bool(self.session.scalar(select(exists().where(at_c.exam_id == exam_id))))

    def uses_question(self, question_id: uuid.UUID) -> bool:
        return bool(self.session.scalar(select(exists().where(eq_c.question_id == question_id))))


class SqlAssignmentRepository(_Repo):
    def get(self, org_id: uuid.UUID, assignment_id: uuid.UUID) -> Assignment | None:
        a = self.session.get(Assignment, assignment_id)
        return a if a is not None and a.organization_id == org_id else None

    def get_any(self, assignment_id: uuid.UUID) -> Assignment | None:
        return self.session.get(Assignment, assignment_id)

    def add(self, a: Assignment, targets: list[AssignmentTarget]) -> None:
        self.session.add(a)
        self.session.flush()
        self.session.add_all(targets)
        self.session.flush()

    def remove(self, a: Assignment) -> None:
        self.session.delete(a)
        self.session.flush()

    def targets(self, assignment_id: uuid.UUID) -> list[AssignmentTarget]:
        return list(self.session.scalars(select(AssignmentTarget).where(t_c.assignment_id == assignment_id)))

    def for_student(self, org_id: uuid.UUID, user_id: uuid.UUID, class_ids: list[uuid.UUID]) -> list[Assignment]:
        a_c = assignments.c
        stmt = (select(Assignment).join(assignment_targets, t_c.assignment_id == a_c.id)
                .where(a_c.organization_id == org_id, or_(t_c.user_id == user_id, t_c.class_id.in_(list(class_ids))))
                .distinct().order_by(a_c.open_at))
        return list(self.session.scalars(stmt))


class SqlAttemptRepository(_Repo):
    def get(self, org_id: uuid.UUID, attempt_id: uuid.UUID) -> Attempt | None:
        att = self.session.get(Attempt, attempt_id)
        return att if att is not None and att.organization_id == org_id else None

    def add(self, att: Attempt) -> None:
        self.session.add(att)
        self.session.flush()

    def of_student(self, assignment_id: uuid.UUID, student_id: uuid.UUID) -> list[Attempt]:
        return list(self.session.scalars(select(Attempt).where(at_c.assignment_id == assignment_id, at_c.student_id == student_id)
                                         .order_by(at_c.started_at.desc())))

    def current(self, assignment_id: uuid.UUID, student_id: uuid.UUID) -> Attempt | None:
        return self.session.scalar(select(Attempt).where(at_c.assignment_id == assignment_id, at_c.student_id == student_id,
                                                         at_c.status == "in_progress"))

    def count(self, assignment_id: uuid.UUID, student_id: uuid.UUID | None = None) -> int:
        stmt = select(func.count()).select_from(attempts).where(at_c.assignment_id == assignment_id)
        if student_id is not None:
            stmt = stmt.where(at_c.student_id == student_id)
        return self.session.scalar(stmt) or 0

    def expired(self, before: datetime) -> list[Attempt]:
        return list(self.session.scalars(select(Attempt).where(at_c.status == "in_progress", at_c.deadline_at < before)))

    def answer(self, attempt_id: uuid.UUID, question_id: uuid.UUID) -> AttemptAnswer | None:
        return self.session.get(AttemptAnswer, (attempt_id, question_id))

    def answers(self, attempt_id: uuid.UUID) -> list[AttemptAnswer]:
        self.session.flush()
        return list(self.session.scalars(select(AttemptAnswer).where(attempt_answers.c.attempt_id == attempt_id)))

    def add_answer(self, ans: AttemptAnswer) -> None:
        self.session.add(ans)

    def count_tab_switch(self, att: Attempt) -> int:
        self.session.execute(update(attempts).where(at_c.id == att.id).values(tab_switches=at_c.tab_switches + 1)
                             .execution_options(synchronize_session=False))
        self.session.refresh(att)
        return att.tab_switches


class SqlAnswerFacts(_Repo):
    def replace(self, attempt_id: uuid.UUID, question_id: uuid.UUID, fact: AnswerFact | None) -> None:
        self.session.execute(delete(AnswerFact).where(AnswerFact.attempt_id == attempt_id, AnswerFact.question_id == question_id))
        if fact is not None:
            self.session.add(fact)
            self.session.flush()

    def earlier(self, student_id: uuid.UUID, question_id: uuid.UUID, attempt_id: uuid.UUID, before: datetime) -> bool:
        return bool(self.session.scalar(select(exists().where(
            f_c.student_id == student_id, f_c.question_id == question_id, f_c.attempt_id != attempt_id,
            at_c.id == f_c.attempt_id, at_c.started_at < before))))
