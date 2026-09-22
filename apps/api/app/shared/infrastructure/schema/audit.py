"""Physical table of the audit log: who changed what (school-years ADR-05). Written through the shared AuditTrail
port (app.shared.infrastructure.sql_audit), read by the audit module."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.shared.infrastructure.db import metadata

audit_logs = Table(
    "audit_logs", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False),
    Column("actor_id", UUID(as_uuid=True), ForeignKey("users.id")),
    Column("action", String(64), nullable=False),
    Column("target_type", String(32), nullable=False),
    Column("target_id", UUID(as_uuid=True)),
    Column("data", JSONB, nullable=False, default=dict),
)
