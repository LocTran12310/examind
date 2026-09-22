import uuid

from sqlalchemy import ForeignKey, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UserDefinedType

from app.core.db import Base, IdMixin, TimestampMixin

LEVEL_KINDS = ("strand", "topic", "subtopic", "type")
TAG_GROUPS = ("method", "skill", "source", "custom")
MAX_TOPIC_DEPTH = 5


class LtreeType(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw):
        return "LTREE"

    def bind_processor(self, dialect):
        return None

    def result_processor(self, dialect, coltype):
        return None


def topic_label(topic_id: uuid.UUID) -> str:
    """ltree label for a topic: stable across renames (ADR-04)."""
    return "t" + topic_id.hex[:12]


class Subject(IdMixin, Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("organization_id", "code"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(100))
    sort: Mapped[int] = mapped_column(Integer, default=0)


class SchoolLevel(IdMixin, TimestampMixin, Base):
    """Cấp học (THCS, THPT…) owned by an org; grades 'belong' to the level whose range contains them."""
    __tablename__ = "school_levels"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_school_levels_org_code"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    code: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(100))
    grade_from: Mapped[int] = mapped_column(SmallInteger)
    grade_to: Mapped[int] = mapped_column(SmallInteger)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Grade(IdMixin, Base):
    __tablename__ = "grades"
    __table_args__ = (UniqueConstraint("organization_id", "level"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    level: Mapped[int] = mapped_column(SmallInteger)
    name: Mapped[str] = mapped_column(String(50))
    school_level_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("school_levels.id"), index=True)


class Semester(IdMixin, Base):
    __tablename__ = "semesters"
    __table_args__ = (UniqueConstraint("organization_id", "code"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    code: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(50))
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Topic(IdMixin, TimestampMixin, Base):
    __tablename__ = "topics"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"), index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("topics.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    level_kind: Mapped[str] = mapped_column(String(16))
    grade: Mapped[int | None] = mapped_column(SmallInteger)
    path: Mapped[str] = mapped_column(LtreeType())
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Tag(IdMixin, TimestampMixin, Base):
    __tablename__ = "tags"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    group: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(100))
    # None = shared by every subject (nguồn đề, "Có hình vẽ"…) — subject-scoped-bank ADR-03
    subject_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), index=True)
