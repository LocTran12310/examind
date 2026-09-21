"""assets and questions (minimal)

Revision ID: 0004
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("storage_key", sa.String(300), nullable=False),
        sa.Column("mime", sa.String(100), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "questions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("subject_id", pg.UUID(as_uuid=True), sa.ForeignKey("subjects.id")),
        sa.Column("type", sa.String(16), nullable=False, server_default="mcq"),
        sa.Column("stem", sa.Text(), nullable=False, server_default=""),
        sa.Column("options", pg.JSONB(), nullable=False, server_default="[]"),
        sa.Column("answer", pg.JSONB()),
        sa.Column("solution", sa.Text(), nullable=False, server_default=""),
        sa.Column("difficulty", sa.String(8)),
        sa.Column("grade", sa.SmallInteger()),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("source", sa.String(32)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("type in ('mcq','true_false','short_answer','essay')", name="ck_questions_type"),
    )


def downgrade() -> None:
    op.drop_table("questions")
    op.drop_table("assets")
