"""adaptive review: student_topic_mastery, flagged status, flag evidence

Revision ID: 0010
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_topic_mastery",
        sa.Column("student_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("topic_id", pg.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("mastery", sa.Float(), nullable=False),
        sa.Column("answers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_at", sa.DateTime(timezone=True)),
    )
    op.add_column("questions", sa.Column("flag_evidence", pg.JSONB()))
    op.drop_constraint("ck_questions_status", "questions")
    op.create_check_constraint("ck_questions_status", "questions",
                               "status in ('draft','auto_approved','needs_review','approved','rejected','duplicate','flagged')")


def downgrade() -> None:
    op.drop_constraint("ck_questions_status", "questions")
    op.create_check_constraint("ck_questions_status", "questions",
                               "status in ('draft','auto_approved','needs_review','approved','rejected','duplicate')")
    op.drop_column("questions", "flag_evidence")
    op.drop_table("student_topic_mastery")
