"""The Postgres job queue (exam-ingestion ADR-01): the worker claims rows with SKIP LOCKED; modules enqueue into it."""
import uuid

from sqlalchemy import Column, DateTime, Index, Integer, String, Table, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.shared.infrastructure.db import metadata

jobs = Table(
    "jobs", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("kind", String(64), index=True, nullable=False),
    Column("payload", JSONB, nullable=False, default=dict),
    Column("status", String(16), nullable=False, default="queued"),  # queued | running | done | failed
    Column("attempts", Integer, nullable=False, default=0),
    Column("max_attempts", Integer, nullable=False, default=3),
    Column("run_after", DateTime(timezone=True)),
    Column("locked_at", DateTime(timezone=True)),
    Column("locked_by", String(100)),
    Column("error", Text),
    Column("finished_at", DateTime(timezone=True)),
)

# indexes the migrations create (declared here so the metadata matches the database; `alembic check` is empty)
Index("ix_jobs_claim", jobs.c.status, jobs.c.run_after, jobs.c.created_at)
