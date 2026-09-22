"""What analytics needs from storage and from the other contexts (the taxonomy's topics, the bank's usable questions,
assessment's exams and attempts), each behind a port. The classes and members a report lists are an application
port (application/ports.py)."""
from collections.abc import Iterable
from datetime import datetime
from typing import Protocol
import uuid

from app.modules.analytics.domain.entities import TopicMastery
from app.modules.analytics.domain.value_objects import AnswerRecord, PracticeAttempt, ReviewStatus, TopicNode


class MasteryRepository(Protocol):
    def get(self, student_id: uuid.UUID, topic_id: uuid.UUID) -> TopicMastery | None: ...

    def add(self, row: TopicMastery) -> None: ...

    def leaves(self, org_id: uuid.UUID, student_id: uuid.UUID) -> list[tuple[TopicMastery, TopicNode]]:
        """The student's mastery rows of the org with their topics."""
        ...

    def clear(self, org_id: uuid.UUID | None) -> None:
        """Every row (of the org when given) out, before a replay."""
        ...

    def empty(self) -> bool: ...

    def flush(self) -> None: ...


class Topics(Protocol):
    def id_by_path(self, org_id: uuid.UUID, path: str) -> uuid.UUID | None: ...

    def of_org(self, org_id: uuid.UUID) -> dict[uuid.UUID, TopicNode]: ...

    def get(self, topic_id: uuid.UUID) -> TopicNode | None: ...

    def strands(self, org_id: uuid.UUID, subject_id: uuid.UUID | None) -> list[TopicNode]:
        """Top-level topics (mạch kiến thức) of the org, of one subject when given."""
        ...


class AnswerHistory(Protocol):
    """The graded answer facts (assessment) a plan and a mastery replay read."""

    def recent_correct(self, org_id: uuid.UUID, student_id: uuid.UUID, since: datetime) -> set[uuid.UUID]:
        """Questions answered fully right since `since`."""
        ...

    def mistakes_to_reask(self, org_id: uuid.UUID, student_id: uuid.UUID, before: datetime, limit: int) -> list[uuid.UUID]:
        """Usable questions answered wrong before `before` and not answered right since, latest mistake first."""
        ...

    def replay(self, org_id: uuid.UUID | None) -> Iterable[AnswerRecord]:
        """Every fact (of the org when given) in grading order."""
        ...

    def empty(self) -> bool: ...


class QuestionPool(Protocol):
    def pool(self, org_id: uuid.UUID, topic_path: str | None, exclude: set, subject_id: uuid.UUID | None = None) -> list[tuple[uuid.UUID, str | None]]:
        """(id, difficulty) of the usable questions of the org (in the topic subtree, of the subject when given), minus `exclude`."""
        ...


class Assessment(Protocol):
    """Exams, assignments and attempts (assessment context) for personal review exams."""

    def create_exam(self, org_id: uuid.UUID, title: str, created_by: uuid.UUID | None, adaptive: dict,
                    question_ids: list[uuid.UUID]) -> uuid.UUID: ...

    def start_attempt(self, org_id: uuid.UUID, exam_id: uuid.UUID, student_id: uuid.UUID, deadline: datetime) -> uuid.UUID: ...

    def assign(self, org_id: uuid.UUID, exam_id: uuid.UUID, student_id: uuid.UUID, title: str, open_at: datetime, close_at: datetime,
               duration_minutes: int, created_by: uuid.UUID | None) -> uuid.UUID: ...

    def practice_attempts(self, student_id: uuid.UUID, limit: int) -> list[PracticeAttempt]: ...

    def latest_review(self, student_id: uuid.UUID) -> ReviewStatus | None: ...
