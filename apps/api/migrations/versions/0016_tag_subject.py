"""Tags may belong to a subject; no subject = shared (subject-scoped-bank ADR-03).

Revision ID: 0016
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0016"
down_revision = "0015"


def upgrade() -> None:
    op.add_column("tags", sa.Column("subject_id", pg.UUID(as_uuid=True), sa.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_tags_subject_id", "tags", ["subject_id"])
    # a tag whose questions all share one subject belongs to it; source tags stay shared
    op.execute("""
        update tags t set subject_id = s.subject_id
        from (
            select qt.tag_id, min(q.subject_id::text)::uuid as subject_id
            from question_tags qt join questions q on q.id = qt.question_id
            group by qt.tag_id
            having count(distinct q.subject_id) = 1 and bool_and(q.subject_id is not null)
        ) s
        where s.tag_id = t.id and t."group" <> 'source'
    """)


def downgrade() -> None:
    op.drop_index("ix_tags_subject_id", table_name="tags")
    op.drop_column("tags", "subject_id")
