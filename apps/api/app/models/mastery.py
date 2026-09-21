from datetime import datetime
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class StudentTopicMastery(Base):
    __tablename__ = "student_topic_mastery"

    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    topic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    mastery: Mapped[float] = mapped_column(Float)
    answers: Mapped[int] = mapped_column(Integer, default=0)
    last_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
