"""Physical tables of the academic area: school years, terms, classes and their members (ADR-01)."""
import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, SmallInteger, String, Table, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db import metadata

# Năm học of one org; exactly one is active (school-years A-01)
school_years = Table(
    "school_years", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False),
    Column("code", String(9), nullable=False),
    Column("name", String(100), nullable=False),
    Column("start_date", Date, nullable=False),
    Column("end_date", Date, nullable=False),
    Column("status", String(16), nullable=False, default="planning"),
    UniqueConstraint("organization_id", "code", name="uq_school_years_org_code"),
)

school_terms = Table(
    "school_terms", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("school_year_id", UUID(as_uuid=True), ForeignKey("school_years.id", ondelete="CASCADE"), index=True, nullable=False),
    Column("code", String(8), nullable=False),
    Column("name", String(50), nullable=False),
    Column("start_date", Date, nullable=False),
    Column("end_date", Date, nullable=False),
    UniqueConstraint("school_year_id", "code", name="uq_school_terms_year_code"),
)

classes = Table(
    "classes", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False),
    Column("name", String(100), nullable=False),
    Column("grade", SmallInteger),  # cache of grades.level for bank/exam filters
    Column("grade_id", UUID(as_uuid=True), ForeignKey("grades.id"), index=True),
    Column("school_year", String(9), nullable=False),  # "2026-2027" — cache of school_years.code
    Column("school_year_id", UUID(as_uuid=True), ForeignKey("school_years.id"), index=True),
    UniqueConstraint("organization_id", "name", "school_year", name="uq_classes_org_name_year"),
)

class_members = Table(
    "class_members", metadata,
    Column("class_id", UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True),
    # enrollment (school-years A-05): active | promoted | retained | transferred | graduated
    Column("status", String(16), nullable=False, default="active", server_default="active"),
    Column("joined_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("left_at", DateTime(timezone=True)),
)

# indexes the migrations create (declared here so the metadata matches the database; `alembic check` is empty)
Index("uq_school_years_one_active", school_years.c.organization_id, unique=True, postgresql_where=text("status = 'active'"))
