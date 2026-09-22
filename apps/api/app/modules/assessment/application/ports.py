"""Read ports of assessment: the exam and assignment lists, an exam's question table, the people and answers reports show."""
from typing import Protocol
import uuid

from app.modules.assessment.application.dto import (
    AssignmentRow, ExamQuestionRow, ExamSummary, Person, PersonalReviewRow, PracticeAttemptRow,
)
from app.modules.assessment.domain.entities import Attempt, AttemptAnswer
from app.shared.application.search import Page, SearchRequest


class ExamReader(Protocol):
    def search(self, org_id: uuid.UUID, req: SearchRequest) -> Page[ExamSummary]:
        """Exams of the org except personal review ones, newest first. Filters: title (text) · grade (number) ·
        source (enum) · subject_id (uuid) · created_at (date); sort also by question_count, total_points."""
        ...

    def questions(self, exam_id: uuid.UUID, req: SearchRequest) -> Page[ExamQuestionRow]:
        """One exam's questions, by position. Filters: stem (text) · type, section (enum) · position, points (number)."""
        ...


class AssignmentReader(Protocol):
    def search(self, org_id: uuid.UUID, req: SearchRequest) -> Page[AssignmentRow]:
        """Newest window first, with the students who submitted and the target classes' names. Filters: title (text) ·
        exam_id (uuid) · open_at, close_at (date) · duration_minutes (number)."""
        ...


class ResultReader(Protocol):
    def attempts(self, assignment_id: uuid.UUID) -> list[Attempt]:
        """Every attempt of the assignment, oldest first."""
        ...

    def answers(self, attempt_ids: list[uuid.UUID]) -> list[AttemptAnswer]: ...

    def people(self, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, Person]: ...


class PersonalReader(Protocol):
    """Personal review exams (source adaptive): a student's practice attempts and the latest review assigned."""

    def practice_attempts(self, org_id: uuid.UUID, student_id: uuid.UUID, limit: int) -> list[PracticeAttemptRow]:
        """The student's attempts outside any assignment, newest first."""
        ...

    def latest_review(self, org_id: uuid.UUID, student_id: uuid.UUID) -> PersonalReviewRow | None:
        """The newest assignment of a personal review exam targeting the student."""
        ...
