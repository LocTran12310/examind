from dataclasses import dataclass, field
from datetime import datetime
import uuid

USABLE = ("auto_approved", "approved")  # the bank's questions an exam may use


@dataclass(frozen=True)
class TopicNode:
    """A topic of the knowledge tree (taxonomy) as analytics sees it."""
    id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    path: str
    subject_id: uuid.UUID | None = None


@dataclass(frozen=True)
class AnswerRecord:
    """One graded answer (an assessment answer fact), as far as mastery is concerned."""
    organization_id: uuid.UUID
    student_id: uuid.UUID
    topic_path: str | None
    correct_ratio: float
    difficulty: str | None
    at: datetime | None


@dataclass(frozen=True)
class Member:
    """A person of a class or the org (identity), with their role in the org."""
    id: uuid.UUID
    full_name: str
    username: str
    is_active: bool = True
    role: str | None = None


@dataclass
class Pick:
    question_id: uuid.UUID
    reason: str
    topic: str | None = None


@dataclass
class Plan:
    """The questions of a personal review exam and why each was chosen."""
    picks: list[Pick] = field(default_factory=list)
    note: str | None = None

    def ids(self) -> set:
        return {p.question_id for p in self.picks}


@dataclass(frozen=True)
class PracticeAttempt:
    """A personal practice attempt with its exam's title and settings (the plan)."""
    attempt_id: uuid.UUID
    title: str
    status: str
    started_at: datetime | None
    submitted_at: datetime | None
    score10: float | None
    settings: dict
    #: the subject the exam was drawn inside; None for runs from before an exam recorded one
    subject_id: uuid.UUID | None = None


@dataclass(frozen=True)
class ReviewStatus:
    assignment_id: uuid.UUID
    title: str
    status: str
    open_at: datetime
    close_at: datetime
    #: personal review papers this student has been given altogether, not just this one
    total: int
