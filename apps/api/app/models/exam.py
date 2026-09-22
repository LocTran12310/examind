"""Exams, assignments, attempts and graded answer facts (exam-practice)."""
from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, IdMixin, TimestampMixin
from app.models.taxonomy import LtreeType

RESULTS_POLICIES = ("after_submit", "after_close", "never")
DEFAULT_POINTS = {"mcq": 0.25, "true_false": 1.0, "short_answer": 0.5, "essay": 1.0}
SECTION_OF_TYPE = {"mcq": "I", "true_false": "II", "short_answer": "III", "essay": "IV"}


class Exam(IdMixin, TimestampMixin, Base):
    __tablename__ = "exams"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    subject_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    grade: Mapped[int | None] = mapped_column(SmallInteger)
    description: Mapped[str] = mapped_column(Text, default="")
    settings: Mapped[dict] = mapped_column(JSONB, default=lambda: {"points_by_type": dict(DEFAULT_POINTS), "scale_to": 10})
    blueprint: Mapped[list] = mapped_column(JSONB, default=list)
    source: Mapped[str] = mapped_column(String(16), default="manual")  # manual | blueprint | adaptive
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    exam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), primary_key=True)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id"), primary_key=True, index=True)
    position: Mapped[int] = mapped_column(Integer)
    section: Mapped[str] = mapped_column(String(8), default="I")
    points: Mapped[float] = mapped_column(Float)
    row: Mapped[int | None] = mapped_column(Integer)  # blueprint row that drew it


class Assignment(IdMixin, TimestampMixin, Base):
    __tablename__ = "assignments"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    exam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    open_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    close_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=True)
    shuffle_options: Mapped[bool] = mapped_column(Boolean, default=True)
    results_policy: Mapped[str] = mapped_column(String(16), default="after_submit")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))


class AssignmentTarget(IdMixin, Base):
    __tablename__ = "assignment_targets"

    assignment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    class_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))


class Attempt(IdMixin, Base):
    __tablename__ = "attempts"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    exam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="in_progress")  # in_progress | submitted
    score: Mapped[float | None] = mapped_column(Float)
    max_score: Mapped[float | None] = mapped_column(Float)
    needs_grading: Mapped[bool] = mapped_column(Boolean, default=False)
    question_order: Mapped[list] = mapped_column(JSONB, default=list)
    option_orders: Mapped[dict] = mapped_column(JSONB, default=dict)
    tab_switches: Mapped[int] = mapped_column(Integer, default=0)


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("attempts.id", ondelete="CASCADE"), primary_key=True)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id"), primary_key=True)
    response: Mapped[dict | None] = mapped_column(JSONB)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    points: Mapped[float | None] = mapped_column(Float)
    max_points: Mapped[float] = mapped_column(Float, default=0)
    key_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    comment: Mapped[str | None] = mapped_column(Text)
    graded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AnswerFact(IdMixin, TimestampMixin, Base):
    """One graded answer, denormalised for reporting (exam-practice ADR-01)."""

    __tablename__ = "answer_facts"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("attempts.id", ondelete="CASCADE"), index=True)
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    exam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    topic_path: Mapped[str | None] = mapped_column(LtreeType())
    tag_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    qtype: Mapped[str] = mapped_column(String(16))
    difficulty: Mapped[str | None] = mapped_column(String(8))
    points: Mapped[float] = mapped_column(Float)
    max_points: Mapped[float] = mapped_column(Float)
    correct_ratio: Mapped[float] = mapped_column(Float)  # points / max_points (0..1)
    # snapshot at grading time so reports do not follow students to later classes (school-years ADR-02)
    school_year_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("school_years.id"), index=True)
    term_code: Mapped[str | None] = mapped_column(String(8))
    class_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list, server_default="{}")
