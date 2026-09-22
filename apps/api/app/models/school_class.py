from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, IdMixin, TimestampMixin


class SchoolClass(IdMixin, TimestampMixin, Base):
    __tablename__ = "classes"
    __table_args__ = (UniqueConstraint("organization_id", "name", "school_year", name="uq_classes_org_name_year"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    grade: Mapped[int | None] = mapped_column(SmallInteger)  # cache of grades.level for bank/exam filters
    grade_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("grades.id"), index=True)
    school_year: Mapped[str] = mapped_column(String(9))  # "2026-2027" — cache of school_years.code
    school_year_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("school_years.id"), index=True)


class ClassMember(Base):
    __tablename__ = "class_members"

    class_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    # enrollment (school-years A-05): active | promoted | retained | transferred | graduated
    status: Mapped[str] = mapped_column(String(16), default="active", server_default="active")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
