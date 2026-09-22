"""Physical tables of the taxonomy area (architecture-refactor ADR-01)."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, SmallInteger, String, Table, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import UserDefinedType

from app.shared.infrastructure.db import metadata


class LtreeType(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw):
        return "LTREE"

    def bind_processor(self, dialect):
        return None

    def result_processor(self, dialect, coltype):
        return None


def _id() -> Column:
    return Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _org() -> Column:
    return Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False)


def _created() -> Column:
    return Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)


tags = Table(
    "tags", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False),
    Column("group", String(16), nullable=False),
    Column("name", String(100), nullable=False),
    # None = shared by every subject (nguồn đề, "Có hình vẽ"…)
    Column("subject_id", UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), index=True),
)

subjects = Table(
    "subjects", metadata, _id(), _org(),
    Column("code", String(32), nullable=False),
    Column("name", String(100), nullable=False),
    Column("sort", Integer, nullable=False, default=0),
    UniqueConstraint("organization_id", "code"),
)

# Cấp học (THCS, THPT…) owned by an org; grades 'belong' to the level whose range contains them
school_levels = Table(
    "school_levels", metadata, _id(), _created(), _org(),
    Column("code", String(20), nullable=False),
    Column("name", String(100), nullable=False),
    Column("grade_from", SmallInteger, nullable=False),
    Column("grade_to", SmallInteger, nullable=False),
    Column("sort", Integer, nullable=False, default=0),
    UniqueConstraint("organization_id", "code", name="uq_school_levels_org_code"),
)

grades = Table(
    "grades", metadata, _id(), _org(),
    Column("level", SmallInteger, nullable=False),
    Column("name", String(50), nullable=False),
    Column("school_level_id", UUID(as_uuid=True), ForeignKey("school_levels.id"), index=True),
    UniqueConstraint("organization_id", "level"),
)

semesters = Table(
    "semesters", metadata, _id(), _org(),
    Column("code", String(16), nullable=False),
    Column("name", String(50), nullable=False),
    Column("sort", Integer, nullable=False, default=0),
    UniqueConstraint("organization_id", "code"),
)

# the knowledge tree: `path` is an ltree of stable labels (topic_label), so renames never touch it
topics = Table(
    "topics", metadata, _id(), _created(), _org(),
    Column("subject_id", UUID(as_uuid=True), ForeignKey("subjects.id"), index=True, nullable=False),
    Column("parent_id", UUID(as_uuid=True), ForeignKey("topics.id"), index=True),
    Column("name", String(200), nullable=False),
    Column("level_kind", String(16), nullable=False),
    Column("grade", SmallInteger),
    Column("path", LtreeType(), nullable=False),
    Column("sort", Integer, nullable=False, default=0),
)
