"""review workflow: statuses, duplicate_of, search_text, spot checks, review_events, trigram search

Revision ID: 0007
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    with op.batch_alter_table("questions") as b:
        b.add_column(sa.Column("duplicate_of", pg.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="SET NULL")))
        b.add_column(sa.Column("search_text", sa.Text(), nullable=False, server_default=""))
        b.add_column(sa.Column("spot_check", sa.Boolean(), nullable=False, server_default=sa.false()))
        b.add_column(sa.Column("reviewed_by", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")))
        b.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True)))
        b.add_column(sa.Column("updated_at", sa.DateTime(timezone=True)))
        b.create_check_constraint("ck_questions_status", "status in ('draft','auto_approved','needs_review','approved','rejected','duplicate')")
    op.execute("CREATE INDEX ix_questions_search_trgm ON questions USING gin (search_text gin_trgm_ops)")
    with op.batch_alter_table("source_documents") as b:
        b.add_column(sa.Column("assigned_to", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")))
    op.create_table(
        "review_events",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("question_id", pg.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="SET NULL"), index=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("before", pg.JSONB()),
        sa.Column("after", pg.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    # legacy drafts are re-triaged by the api on boot (app.seed.bootstrap → triage_legacy_drafts)


def downgrade() -> None:
    op.drop_table("review_events")
    with op.batch_alter_table("source_documents") as b:
        b.drop_column("assigned_to")
    op.execute("DROP INDEX IF EXISTS ix_questions_search_trgm")
    with op.batch_alter_table("questions") as b:
        b.drop_constraint("ck_questions_status")
        for c in ("updated_at", "reviewed_at", "reviewed_by", "spot_check", "search_text", "duplicate_of"):
            b.drop_column(c)
