"""The weekly mastery snapshot per student and topic (learning-telemetry A-06).

Empty on upgrade; the bootstrap derives the past weeks from the answer facts and the worker keeps the running week.

Revision ID: 0018
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_topic_week",
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("topic_id", UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("week_start", sa.Date(), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("mastery", sa.Float(), nullable=False),
        sa.Column("answers", sa.Integer(), nullable=False),
    )
    op.create_index("ix_student_topic_week_organization_id", "student_topic_week", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_student_topic_week_organization_id", table_name="student_topic_week")
    op.drop_table("student_topic_week")
