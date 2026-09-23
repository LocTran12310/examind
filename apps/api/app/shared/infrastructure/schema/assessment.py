"""Physical tables of assessment: exams and their questions, assignments and their targets, attempts, answers and the
graded answer facts reports read (ADR-01). The assessment module maps its dataclasses onto them; analytics reads
answer_facts through SQL."""
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from app.shared.infrastructure.db import metadata
from app.shared.infrastructure.schema.taxonomy import LtreeType


def _id() -> Column:
    return Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created() -> Column:
    return Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)


def _org() -> Column:
    return Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False)


exams = Table(
    "exams", metadata,
    _id(),
    _created(),
    _org(),
    Column("title", String(200), nullable=False),
    Column("subject_id", UUID(as_uuid=True), ForeignKey("subjects.id")),
    Column("grade", SmallInteger),
    Column("description", Text, nullable=False, default=""),
    Column("settings", JSONB, nullable=False),  # points_by_type, scale_to, source_document_id, duration_minutes, adaptive
    Column("blueprint", JSONB, nullable=False, default=list),
    Column("source", String(16), nullable=False, default="manual"),  # manual | blueprint | adaptive | document
    Column("created_by", UUID(as_uuid=True), ForeignKey("users.id")),
    Column("updated_at", DateTime(timezone=True), onupdate=func.now()),
)

exam_questions = Table(
    "exam_questions", metadata,
    Column("exam_id", UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), primary_key=True),
    Column("question_id", UUID(as_uuid=True), ForeignKey("questions.id"), primary_key=True, index=True),
    Column("position", Integer, nullable=False),
    Column("section", String(8), nullable=False, default="I"),
    Column("points", Float, nullable=False),
    Column("row", Integer),  # blueprint row that drew it
)

assignments = Table(
    "assignments", metadata,
    _id(),
    _created(),
    _org(),
    Column("exam_id", UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), index=True, nullable=False),
    Column("title", String(200), nullable=False),
    Column("open_at", DateTime(timezone=True), nullable=False),
    Column("close_at", DateTime(timezone=True), nullable=False),
    Column("duration_minutes", Integer, nullable=False),
    Column("max_attempts", Integer, nullable=False, default=1),
    Column("shuffle_questions", Boolean, nullable=False, default=True),
    Column("shuffle_options", Boolean, nullable=False, default=True),
    Column("results_policy", String(16), nullable=False, default="after_submit"),
    Column("created_by", UUID(as_uuid=True), ForeignKey("users.id")),
    CheckConstraint("close_at > open_at", name="ck_assignments_window"),
    CheckConstraint("results_policy in ('after_submit','after_close','never')", name="ck_assignments_policy"),
)

assignment_targets = Table(
    "assignment_targets", metadata,
    _id(),
    Column("assignment_id", UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), index=True, nullable=False),
    Column("class_id", UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE")),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")),
    CheckConstraint("(class_id is null) <> (user_id is null)", name="ck_targets_one"),
)

attempts = Table(
    "attempts", metadata,
    _id(),
    _org(),
    Column("assignment_id", UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), index=True),
    Column("exam_id", UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), index=True, nullable=False),
    Column("student_id", UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False),
    Column("started_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("deadline_at", DateTime(timezone=True), nullable=False),
    Column("submitted_at", DateTime(timezone=True)),
    Column("status", String(16), nullable=False, default="in_progress"),  # in_progress | submitted
    Column("score", Float),
    Column("max_score", Float),
    Column("needs_grading", Boolean, nullable=False, default=False),
    Column("question_order", JSONB, nullable=False, default=list),
    Column("option_orders", JSONB, nullable=False, default=dict),
    Column("tab_switches", Integer, nullable=False, default=0),
)

attempt_answers = Table(
    "attempt_answers", metadata,
    Column("attempt_id", UUID(as_uuid=True), ForeignKey("attempts.id", ondelete="CASCADE"), primary_key=True),
    Column("question_id", UUID(as_uuid=True), ForeignKey("questions.id"), primary_key=True),
    Column("response", JSONB),
    Column("is_correct", Boolean),
    Column("points", Float),
    Column("max_points", Float, nullable=False, default=0),
    Column("key_snapshot", JSONB),  # the key used for grading (exam-practice ADR-03)
    Column("comment", Text),
    Column("graded_by", UUID(as_uuid=True), ForeignKey("users.id")),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    # what the runner reports while the question is on screen (learning-telemetry ADR-01)
    Column("first_seen_at", DateTime(timezone=True)),
    Column("answered_at", DateTime(timezone=True)),
    Column("seconds_spent", Integer, nullable=False, default=0),
    Column("save_count", Integer, nullable=False, default=0),
)

# one graded answer, denormalised for reporting (exam-practice ADR-01)
answer_facts = Table(
    "answer_facts", metadata,
    _id(),
    _created(),
    _org(),
    Column("attempt_id", UUID(as_uuid=True), ForeignKey("attempts.id", ondelete="CASCADE"), index=True, nullable=False),
    Column("assignment_id", UUID(as_uuid=True), index=True),
    Column("exam_id", UUID(as_uuid=True), nullable=False),
    Column("student_id", UUID(as_uuid=True), index=True, nullable=False),
    Column("question_id", UUID(as_uuid=True), index=True, nullable=False),
    Column("topic_path", LtreeType()),
    Column("tag_ids", ARRAY(UUID(as_uuid=True)), nullable=False, default=list),
    Column("qtype", String(16), nullable=False),
    Column("difficulty", String(8)),
    Column("points", Float, nullable=False),
    Column("max_points", Float, nullable=False),
    Column("correct_ratio", Float, nullable=False),  # points / max_points (0..1)
    # snapshot at grading time so reports do not follow students to later classes (school-years ADR-02)
    Column("school_year_id", UUID(as_uuid=True), ForeignKey("school_years.id"), index=True),
    Column("term_code", String(8)),
    Column("class_ids", ARRAY(UUID(as_uuid=True)), nullable=False, default=list, server_default="{}"),
    # the answer's own evidence, copied from attempt_answers (learning-telemetry ADR-01)
    Column("seconds_spent", Integer),
    Column("answered_at", DateTime(timezone=True)),
    Column("first_attempt", Boolean),
)

# indexes the migrations create (declared here so the metadata matches the database; `alembic check` is empty)
Index("ix_answer_facts_student_question", answer_facts.c.student_id, answer_facts.c.question_id, answer_facts.c.created_at)
Index("ix_answer_facts_class_ids", answer_facts.c.class_ids, postgresql_using="gin")
Index("ix_answer_facts_tags", answer_facts.c.tag_ids, postgresql_using="gin")
Index("ix_answer_facts_topic", answer_facts.c.topic_path, postgresql_using="gist")
Index("ix_attempts_open", attempts.c.status, attempts.c.deadline_at)
