import uuid

from sqlalchemy import Float, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, IdMixin, TimestampMixin

QUESTION_TYPES = ("mcq", "true_false", "short_answer", "essay")
DIFFICULTIES = ("nb", "th", "vd", "vdc")


class Question(IdMixin, TimestampMixin, Base):
    """Full question content: stem, options, answer, solution — markdown + LaTeX + `asset:<id>` images."""

    __tablename__ = "questions"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    type: Mapped[str] = mapped_column(String(16), default="mcq")
    stem: Mapped[str] = mapped_column(Text, default="")
    # mcq: [{label, content}], true_false: [{label, content, is_true}]
    options: Mapped[list] = mapped_column(JSONB, default=list)
    # mcq: {"key": "C"}; true_false: {"a": true, ...}; short_answer: {"value": "..."}; essay: {"text": "..."}
    answer: Mapped[dict | None] = mapped_column(JSONB)
    solution: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[str | None] = mapped_column(String(8))
    grade: Mapped[int | None] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    source: Mapped[str | None] = mapped_column(String(32))  # demo | document | manual
    # provenance from ingestion (exam-ingestion)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"), index=True)
    number: Mapped[int | None] = mapped_column(Integer)
    part: Mapped[str | None] = mapped_column(String(16))
    semester_code: Mapped[str | None] = mapped_column(String(16))
    exam_kind: Mapped[str | None] = mapped_column(String(32))
    confidence: Mapped[float | None] = mapped_column(Float)
    issues: Mapped[list] = mapped_column(JSONB, default=list)
    parse_method: Mapped[str | None] = mapped_column(String(16))  # rule | llm | ocr
    parse_model: Mapped[str | None] = mapped_column(String(120))
    answer_source: Mapped[str | None] = mapped_column(String(16))  # inline | key | format | llm
