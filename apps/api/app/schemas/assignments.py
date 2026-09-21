from datetime import datetime
import uuid

from pydantic import BaseModel, Field


class AssignmentIn(BaseModel):
    exam_id: uuid.UUID
    title: str | None = Field(default=None, max_length=200)
    open_at: datetime
    close_at: datetime
    duration_minutes: int
    max_attempts: int = 1
    shuffle_questions: bool = True
    shuffle_options: bool = True
    results_policy: str = "after_submit"
    class_ids: list[uuid.UUID] = []
    user_ids: list[uuid.UUID] = []


class AssignmentPatch(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    open_at: datetime | None = None
    close_at: datetime | None = None
    duration_minutes: int | None = None
    max_attempts: int | None = None
    shuffle_questions: bool | None = None
    shuffle_options: bool | None = None
    results_policy: str | None = None


class AssignmentOut(BaseModel):
    id: uuid.UUID
    exam_id: uuid.UUID
    title: str
    open_at: datetime
    close_at: datetime
    duration_minutes: int
    max_attempts: int
    shuffle_questions: bool
    shuffle_options: bool
    results_policy: str
    students: int = 0
    submitted: int = 0
    classes: list[str] = []


class AttemptBrief(BaseModel):
    id: uuid.UUID
    status: str
    started_at: datetime
    deadline_at: datetime
    submitted_at: datetime | None
    score: float | None
    max_score: float | None
    score10: float | None = None
    needs_grading: bool


class MyAssignmentOut(BaseModel):
    assignment: AssignmentOut
    state: str
    attempts: list[AttemptBrief]
    attempts_left: int


def assignment_out(a, **extra) -> AssignmentOut:
    return AssignmentOut(id=a.id, exam_id=a.exam_id, title=a.title, open_at=a.open_at, close_at=a.close_at, duration_minutes=a.duration_minutes,
                         max_attempts=a.max_attempts, shuffle_questions=a.shuffle_questions, shuffle_options=a.shuffle_options,
                         results_policy=a.results_policy, **extra)


def attempt_brief(t, scale_to: float = 10, show_score: bool = True) -> AttemptBrief:
    from app.services.scoring import scaled

    visible = show_score and t.score is not None
    return AttemptBrief(id=t.id, status=t.status, started_at=t.started_at, deadline_at=t.deadline_at, submitted_at=t.submitted_at,
                        score=t.score if visible else None, max_score=t.max_score, needs_grading=t.needs_grading,
                        score10=scaled(t.score, t.max_score or 0, scale_to) if visible else None)
