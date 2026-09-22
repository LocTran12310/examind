"""Columns of other contexts' tables the bank reads (SQLAlchemy Core, ADR-01): source documents (ingestion) and
submitted answers (assessment). Lightweight tables: they are not part of the metadata."""
from sqlalchemy import column, table
from sqlalchemy.dialects.postgresql import JSONB, UUID

source_documents = table(
    "source_documents",
    column("id", UUID(as_uuid=True)), column("organization_id", UUID(as_uuid=True)), column("filename"), column("mime"), column("size"),
    column("status"), column("error"), column("metadata", JSONB), column("processing_config", JSONB), column("page_count"),
    column("question_count"), column("log", JSONB), column("created_at"), column("finished_at"), column("assigned_to", UUID(as_uuid=True)),
)

attempts = table(
    "attempts",
    column("id", UUID(as_uuid=True)), column("status"), column("score"), column("max_score"),
)

attempt_answers = table(
    "attempt_answers",
    column("attempt_id", UUID(as_uuid=True)), column("question_id", UUID(as_uuid=True)), column("response", JSONB), column("points"),
)
