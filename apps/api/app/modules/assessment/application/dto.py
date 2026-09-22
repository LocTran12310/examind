from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.modules.assessment.domain.entities import Assignment, Attempt, Exam
from app.modules.assessment.domain.services.scoring import scaled


@dataclass(frozen=True)
class ExamQuestionView:
    question: dict  # the bank's view of the question (content, provenance, topics, tags)
    position: int
    section: str
    points: float
    row: int | None


@dataclass(frozen=True)
class ExamView:
    exam: Exam
    question_count: int
    total_points: float
    questions: list[ExamQuestionView] = field(default_factory=list)  # empty in lists


@dataclass(frozen=True)
class ExamSummary:
    """A row of the exam list: the exam with its question count and total points."""
    exam: Exam
    question_count: int
    total_points: float


@dataclass(frozen=True)
class ExamQuestionRow:
    question_id: uuid.UUID
    position: int
    section: str
    points: float
    row: int | None


@dataclass(frozen=True)
class AssignmentRow:
    """A row of the assignment list before the student count is added."""
    assignment: Assignment
    submitted: int
    classes: list[str]


@dataclass(frozen=True)
class AssignmentView:
    assignment: Assignment
    students: int = 0
    submitted: int = 0
    classes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AttemptBrief:
    id: uuid.UUID
    status: str
    started_at: datetime | None
    deadline_at: datetime
    submitted_at: datetime | None
    score: float | None
    max_score: float | None
    score10: float | None
    needs_grading: bool


@dataclass(frozen=True)
class MyAssignmentView:
    assignment: Assignment
    state: str
    attempts: list[AttemptBrief]
    attempts_left: int


@dataclass(frozen=True)
class Person:
    id: uuid.UUID
    full_name: str
    username: str


def attempt_brief(t: Attempt, show_score: bool, scale_to: float = 10) -> AttemptBrief:
    visible = show_score and t.score is not None
    return AttemptBrief(id=t.id, status=t.status, started_at=t.started_at, deadline_at=t.deadline_at, submitted_at=t.submitted_at,
                        score=t.score if visible else None, max_score=t.max_score, needs_grading=t.needs_grading,
                        score10=scaled(t.score, t.max_score or 0, scale_to) if visible else None)


@dataclass(frozen=True)
class PracticeAttemptRow:
    """A personal practice attempt (no assignment) with its exam's title and settings (analytics shows the plan)."""
    attempt_id: uuid.UUID
    title: str
    status: str
    started_at: datetime | None
    submitted_at: datetime | None
    score10: float | None  # on a 10 scale, once submitted
    settings: dict


@dataclass(frozen=True)
class PersonalReviewRow:
    """The latest personal review exam assigned to a student and where the student is with it."""
    assignment_id: uuid.UUID
    title: str
    status: str  # not_started | in_progress | submitted
