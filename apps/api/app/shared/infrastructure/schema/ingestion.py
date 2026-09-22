"""Physical tables of ingestion: uploaded files, the images stored from them (and from the editor), the AI model
registry (architecture-refactor ADR-01). The ingestion module maps its dataclasses onto them."""
import uuid

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from app.shared.infrastructure.db import metadata


def _id() -> Column:
    return Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created() -> Column:
    return Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)


source_documents = Table(
    "source_documents", metadata,
    _id(),
    _created(),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False),
    Column("filename", String(300), nullable=False),
    Column("mime", String(100), nullable=False),
    Column("size", BigInteger, nullable=False),
    Column("file_hash", String(64), nullable=False),
    Column("storage_key", String(300), nullable=False),
    Column("status", String(16), nullable=False, default="queued"),  # queued | processing | parsed | failed
    Column("error", Text),
    Column("metadata", JSONB, nullable=False, default=dict),
    Column("processing_config", JSONB, nullable=False, default=dict),
    Column("page_count", Integer),
    Column("question_count", Integer, nullable=False, default=0),
    Column("log", JSONB, nullable=False, default=list),
    Column("uploaded_by", UUID(as_uuid=True), ForeignKey("users.id")),
    Column("assigned_to", UUID(as_uuid=True), ForeignKey("users.id")),
    Column("finished_at", DateTime(timezone=True)),
    UniqueConstraint("organization_id", "file_hash", name="uq_documents_org_hash"),
)

# an image stored in object storage, referenced from markdown as `asset:<id>`
assets = Table(
    "assets", metadata,
    _id(),
    _created(),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False),
    Column("storage_key", String(300), nullable=False),
    Column("mime", String(100), nullable=False),
    Column("size", Integer, nullable=False),
    Column("width", Integer),
    Column("height", Integer),
    Column("source_document_id", UUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"), index=True),
    Column("page", Integer),
)

# a model an org (or, with organization_id NULL, every org) may use for splitting, tagging or OCR
ai_models = Table(
    "ai_models", metadata,
    _id(),
    _created(),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), index=True),
    Column("name", String(100), nullable=False),
    Column("provider", String(16), nullable=False),
    Column("model", String(120), nullable=False),
    Column("base_url", String(300)),
    Column("api_key_enc", Text),
    Column("capabilities", ARRAY(String(16)), nullable=False, default=lambda: ["text"]),
    Column("is_free", Boolean, nullable=False, default=True),
    Column("enabled", Boolean, nullable=False, default=True),
)
