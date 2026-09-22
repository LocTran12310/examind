"""Physical tables of the taxonomy area (architecture-refactor ADR-01)."""
from sqlalchemy import Column, DateTime, ForeignKey, String, Table, func
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db import metadata

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
