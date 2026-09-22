"""What assessment needs from storage and from the other contexts (the bank's questions, the academic classes, the
identity memberships, the taxonomy subjects, analytics' mastery), each behind a port."""
from datetime import datetime
from typing import Protocol
import uuid

from app.modules.assessment.domain.entities import (
    AnswerFact,
    Assignment,
    AssignmentTarget,
    Attempt,
    AttemptAnswer,
    Exam,
    ExamQuestion,
)
from app.modules.assessment.domain.value_objects import PoolFilter, QuestionRef, Snapshot


class ExamRepository(Protocol):
    def get(self, org_id: uuid.UUID, exam_id: uuid.UUID) -> Exam | None: ...

    def get_any(self, exam_id: uuid.UUID) -> Exam | None:
        """By id only (an attempt's exam)."""
        ...

    def add(self, exam: Exam) -> None: ...

    def remove(self, exam: Exam) -> None: ...

    def questions(self, exam_id: uuid.UUID) -> list[ExamQuestion]:
        """The exam's questions by position (after flushing pending changes)."""
        ...

    def question(self, exam_id: uuid.UUID, question_id: uuid.UUID) -> ExamQuestion | None: ...

    def add_question(self, eq: ExamQuestion) -> None: ...

    def remove_question(self, eq: ExamQuestion) -> None:
        """Deleted and flushed (a replacement may take its position)."""
        ...

    def clear(self, exam_id: uuid.UUID) -> None:
        """Every question out (a blueprint that replaces)."""
        ...

    def has_attempts(self, exam_id: uuid.UUID) -> bool: ...

    def uses_question(self, question_id: uuid.UUID) -> bool:
        """Whether any exam uses the question (the bank then refuses to delete it)."""
        ...


class AssignmentRepository(Protocol):
    def get(self, org_id: uuid.UUID, assignment_id: uuid.UUID) -> Assignment | None: ...

    def get_any(self, assignment_id: uuid.UUID) -> Assignment | None: ...

    def add(self, a: Assignment, targets: list[AssignmentTarget]) -> None: ...

    def remove(self, a: Assignment) -> None: ...

    def targets(self, assignment_id: uuid.UUID) -> list[AssignmentTarget]: ...

    def for_student(self, org_id: uuid.UUID, user_id: uuid.UUID, class_ids: list[uuid.UUID]) -> list[Assignment]:
        """Assignments of the org targeting the student or one of these classes, by open time."""
        ...


class AttemptRepository(Protocol):
    def get(self, org_id: uuid.UUID, attempt_id: uuid.UUID) -> Attempt | None: ...

    def add(self, att: Attempt) -> None: ...

    def of_student(self, assignment_id: uuid.UUID, student_id: uuid.UUID) -> list[Attempt]:
        """Newest first."""
        ...

    def current(self, assignment_id: uuid.UUID, student_id: uuid.UUID) -> Attempt | None:
        """The student's attempt in progress."""
        ...

    def count(self, assignment_id: uuid.UUID, student_id: uuid.UUID | None = None) -> int: ...

    def expired(self, before: datetime) -> list[Attempt]:
        """Attempts in progress whose deadline is before `before`."""
        ...

    def answer(self, attempt_id: uuid.UUID, question_id: uuid.UUID) -> AttemptAnswer | None: ...

    def answers(self, attempt_id: uuid.UUID) -> list[AttemptAnswer]: ...

    def add_answer(self, ans: AttemptAnswer) -> None: ...

    def count_tab_switch(self, att: Attempt) -> int:
        """Atomically one more; the new count."""
        ...

    def flush(self) -> None: ...


class AnswerFacts(Protocol):
    def replace(self, attempt_id: uuid.UUID, question_id: uuid.UUID, fact: AnswerFact | None) -> None:
        """The fact of that answer becomes `fact` (None: none, e.g. an essay not graded yet)."""
        ...


class QuestionBank(Protocol):
    """The bank context, seen from assessment."""

    def questions(self, org_id: uuid.UUID | None, ids: list[uuid.UUID]) -> list[QuestionRef]:
        """Questions among `ids` (of the org when given)."""
        ...

    def of_document(self, document_id: uuid.UUID) -> list[QuestionRef]: ...

    def pool(self, org_id: uuid.UUID, f: PoolFilter) -> list[uuid.UUID]:
        """Usable questions of the org the filter selects, by id (a draw with a seed is repeatable)."""
        ...

    def views(self, org_id: uuid.UUID | None, ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
        """The bank's full view of each question (content, provenance, topics with the primary first, tags)."""
        ...

    def classification(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[str | None, list[uuid.UUID]]]:
        """{question id: (ltree path of its primary topic, its tag ids)} — what an answer fact records."""
        ...


class Roster(Protocol):
    """Classes (academic context) and memberships (identity context) as assignments see them."""

    def class_names(self, org_id: uuid.UUID, class_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """The classes of the org among `class_ids`."""
        ...

    def class_members(self, org_id: uuid.UUID, class_ids: list[uuid.UUID]) -> set[uuid.UUID]: ...

    def classes_of(self, org_id: uuid.UUID, user_id: uuid.UUID) -> list[uuid.UUID]: ...

    def students(self, org_id: uuid.UUID, user_ids: set[uuid.UUID], active_accounts: bool = False) -> set[uuid.UUID]:
        """Those with an active student membership in the org (and, with active_accounts, an active account)."""
        ...

    def snapshot(self, org_id: uuid.UUID, student_id: uuid.UUID, when: datetime) -> Snapshot:
        """The school year covering `when` (else the active one), its term then and the student's classes of that year."""
        ...


class Subjects(Protocol):
    def exists(self, org_id: uuid.UUID, subject_id: uuid.UUID) -> bool: ...


class FactListener(Protocol):
    """Told about every new answer fact, in grading order (analytics keeps the topic mastery from them)."""

    def recorded(self, fact: AnswerFact) -> None: ...
