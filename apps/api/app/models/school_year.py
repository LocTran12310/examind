from datetime import date
import uuid

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, IdMixin, TimestampMixin

YEAR_STATUSES = ("planning", "active", "closed")
TERMS = (("hk1", "Học kỳ 1"), ("hk2", "Học kỳ 2"))


class SchoolYear(IdMixin, TimestampMixin, Base):
    """Năm học of one org; exactly one is active (school-years A-01)."""
    __tablename__ = "school_years"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_school_years_org_code"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(9))
    name: Mapped[str] = mapped_column(String(100))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), default="planning")

    terms: Mapped[list["SchoolTerm"]] = relationship(order_by="SchoolTerm.code", cascade="all, delete-orphan", lazy="selectin")


class SchoolTerm(IdMixin, Base):
    __tablename__ = "school_terms"
    __table_args__ = (UniqueConstraint("school_year_id", "code", name="uq_school_terms_year_code"),)

    school_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("school_years.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(8))
    name: Mapped[str] = mapped_column(String(50))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
