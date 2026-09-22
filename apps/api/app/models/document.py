from datetime import datetime
import uuid

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, IdMixin, TimestampMixin

DOC_STATUSES = ("queued", "processing", "parsed", "failed")


class SourceDocument(IdMixin, TimestampMixin, Base):
    __tablename__ = "source_documents"
    __table_args__ = (UniqueConstraint("organization_id", "file_hash", name="uq_documents_org_hash"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    filename: Mapped[str] = mapped_column(String(300))
    mime: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(BigInteger)
    file_hash: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(16), default="queued")
    error: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    processing_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    page_count: Mapped[int | None] = mapped_column(Integer)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    log: Mapped[list] = mapped_column(JSONB, default=list)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# question links moved to the bank module (architecture-refactor ADR-01); re-exported for the old layout
from app.modules.bank.domain.entities import QuestionTag, QuestionTopic  # noqa: E402,F401
from app.modules.bank.infrastructure import orm as _bank_orm  # noqa: E402,F401
