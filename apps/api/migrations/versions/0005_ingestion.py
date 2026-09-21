"""ingestion: jobs, source_documents, question provenance, question_topics/tags

Revision ID: 0005
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(64), nullable=False, index=True),
        sa.Column("payload", pg.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("run_after", sa.DateTime(timezone=True)),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column("locked_by", sa.String(100)),
        sa.Column("error", sa.Text()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_jobs_claim", "jobs", ["status", "run_after", "created_at"])
    op.create_table(
        "source_documents",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("filename", sa.String(300), nullable=False),
        sa.Column("mime", sa.String(100), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(300), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("error", sa.Text()),
        sa.Column("metadata", pg.JSONB(), nullable=False, server_default="{}"),
        sa.Column("processing_config", pg.JSONB(), nullable=False, server_default="{}"),
        sa.Column("page_count", sa.Integer()),
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("log", pg.JSONB(), nullable=False, server_default="[]"),
        sa.Column("uploaded_by", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "file_hash", name="uq_documents_org_hash"),
    )
    with op.batch_alter_table("questions") as b:
        b.add_column(sa.Column("source_document_id", pg.UUID(as_uuid=True), sa.ForeignKey("source_documents.id", ondelete="SET NULL")))
        b.add_column(sa.Column("number", sa.Integer()))
        b.add_column(sa.Column("part", sa.String(16)))
        b.add_column(sa.Column("semester_code", sa.String(16)))
        b.add_column(sa.Column("exam_kind", sa.String(32)))
        b.add_column(sa.Column("confidence", sa.Float()))
        b.add_column(sa.Column("issues", pg.JSONB(), nullable=False, server_default="[]"))
        b.add_column(sa.Column("parse_method", sa.String(16)))
        b.add_column(sa.Column("parse_model", sa.String(120)))
        b.add_column(sa.Column("answer_source", sa.String(16)))
    op.create_index("ix_questions_source_document_id", "questions", ["source_document_id"])
    op.create_index("ix_questions_org_status", "questions", ["organization_id", "status"])
    with op.batch_alter_table("assets") as b:
        b.add_column(sa.Column("source_document_id", pg.UUID(as_uuid=True), sa.ForeignKey("source_documents.id", ondelete="SET NULL")))
        b.add_column(sa.Column("page", sa.Integer()))
    op.create_index("ix_assets_source_document_id", "assets", ["source_document_id"])
    op.create_table(
        "question_topics",
        sa.Column("question_id", pg.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("topic_id", pg.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True, index=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source", sa.String(8), nullable=False, server_default="manual"),
        sa.Column("score", sa.Float()),
    )
    op.execute("CREATE UNIQUE INDEX uq_question_topics_primary ON question_topics (question_id) WHERE is_primary")
    op.create_table(
        "question_tags",
        sa.Column("question_id", pg.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", pg.UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True),
    )


def downgrade() -> None:
    op.drop_table("question_tags")
    op.drop_table("question_topics")
    op.drop_index("ix_assets_source_document_id", "assets")
    with op.batch_alter_table("assets") as b:
        b.drop_column("page")
        b.drop_column("source_document_id")
    op.drop_index("ix_questions_org_status", "questions")
    op.drop_index("ix_questions_source_document_id", "questions")
    with op.batch_alter_table("questions") as b:
        for c in ("answer_source", "parse_model", "parse_method", "issues", "confidence", "exam_kind", "semester_code", "part", "number", "source_document_id"):
            b.drop_column(c)
    op.drop_table("source_documents")
    op.drop_index("ix_jobs_claim", "jobs")
    op.drop_table("jobs")
