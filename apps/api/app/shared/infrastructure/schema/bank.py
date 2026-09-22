"""Physical tables of the question bank: questions, their topic/tag links and the review history (ADR-01).
The bank module maps its dataclasses onto them; other contexts read their columns through SQLAlchemy Core."""
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, SmallInteger, String, Table, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.shared.infrastructure.db import metadata


def _id() -> Column:
    return Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created() -> Column:
    return Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)


# full question content: stem, options, answer, solution — markdown + LaTeX + `asset:<id>` images
questions = Table(
    "questions", metadata,
    _id(),
    _created(),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False),
    Column("subject_id", UUID(as_uuid=True), ForeignKey("subjects.id")),
    Column("type", String(16), nullable=False, default="mcq"),
    Column("stem", Text, nullable=False, default=""),
    # mcq: [{label, content}], true_false: [{label, content, is_true}]
    Column("options", JSONB, nullable=False, default=list),
    # mcq: {"key": "C"}; true_false: {"a": true, ...}; short_answer: {"value": "..."}; essay: {"text": "..."}
    Column("answer", JSONB(none_as_null=True)),
    Column("solution", Text, nullable=False, default=""),
    Column("difficulty", String(8)),
    Column("grade", SmallInteger),
    Column("status", String(20), nullable=False, default="draft"),
    Column("source", String(32)),  # demo | document | manual
    # provenance from ingestion
    Column("source_document_id", UUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"), index=True),
    Column("number", Integer),
    Column("page", Integer),  # first source page (PDF/scan)
    Column("part", String(16)),
    Column("semester_code", String(16)),
    Column("exam_kind", String(32)),
    Column("confidence", Float),
    Column("issues", JSONB, nullable=False, default=list),
    Column("parse_method", String(16)),  # rule | llm | ocr
    Column("parse_model", String(120)),
    Column("answer_source", String(16)),  # inline | key | format | llm | manual
    # review workflow
    Column("duplicate_of", UUID(as_uuid=True), ForeignKey("questions.id", ondelete="SET NULL")),
    Column("search_text", Text, nullable=False, default=""),
    Column("spot_check", Boolean, nullable=False, default=False),
    Column("reviewed_by", UUID(as_uuid=True), ForeignKey("users.id")),
    Column("reviewed_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True), onupdate=func.now()),
    Column("flag_evidence", JSONB(none_as_null=True)),  # key audit
)

question_topics = Table(
    "question_topics", metadata,
    Column("question_id", UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True, index=True),
    Column("is_primary", Boolean, nullable=False, default=False),
    Column("source", String(8), nullable=False, default="manual"),  # auto | ai | manual
    Column("score", Float),
)

question_tags = Table(
    "question_tags", metadata,
    Column("question_id", UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True),
)

# append-only history of review actions; never updated
review_events = Table(
    "review_events", metadata,
    _id(),
    _created(),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False),
    Column("question_id", UUID(as_uuid=True), ForeignKey("questions.id", ondelete="SET NULL"), index=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id")),
    Column("action", String(16), nullable=False),
    Column("before", JSONB(none_as_null=True)),
    Column("after", JSONB(none_as_null=True)),
)

# indexes the migrations create (declared here so the metadata matches the database; `alembic check` is empty)
Index("ix_questions_org_status", questions.c.organization_id, questions.c.status)
Index("uq_question_topics_primary", question_topics.c.question_id, unique=True, postgresql_where=text("is_primary"))
Index("ix_questions_search_trgm", questions.c.search_text, postgresql_using="gin", postgresql_ops={"search_text": "gin_trgm_ops"})
