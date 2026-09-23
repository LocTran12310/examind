"""Physical tables of analytics: the per-topic mastery of each student (adaptive-review ADR-01) and its weekly
snapshot (learning-telemetry A-06). The reports read answer_facts (assessment) through SQL."""
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, Table
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db import metadata

student_topic_mastery = Table(
    "student_topic_mastery", metadata,
    Column("student_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False),
    Column("mastery", Float, nullable=False),
    Column("answers", Integer, nullable=False, default=0),
    Column("last_at", DateTime(timezone=True)),
)

student_topic_week = Table(
    "student_topic_week", metadata,
    Column("student_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
    Column("week_start", Date, primary_key=True),  # Monday of the business week the row closes (A-06)
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False),
    Column("mastery", Float, nullable=False),
    Column("answers", Integer, nullable=False, default=0),
)
