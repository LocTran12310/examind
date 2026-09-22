"""Enrollment status on class_members; answer facts remember year, term and classes (school-years ADR-02).

Revision ID: 0015
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("class_members", sa.Column("status", sa.String(16), nullable=False, server_default="active"))
    op.add_column("class_members", sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("class_members", sa.Column("left_at", sa.DateTime(timezone=True)))
    op.add_column("answer_facts", sa.Column("school_year_id", pg.UUID(as_uuid=True), sa.ForeignKey("school_years.id"), index=True))
    op.add_column("answer_facts", sa.Column("term_code", sa.String(8)))
    op.add_column("answer_facts", sa.Column("class_ids", pg.ARRAY(pg.UUID(as_uuid=True)), nullable=False, server_default="{}"))
    op.create_index("ix_answer_facts_class_ids", "answer_facts", ["class_ids"], postgresql_using="gin")
    # Backfill (best effort): the year containing the answer date, else the org's active year; the term by date;
    # the student's classes in that year.
    op.execute("""
        UPDATE answer_facts f SET school_year_id = COALESCE(
            (SELECT y.id FROM school_years y WHERE y.organization_id = f.organization_id
                AND f.created_at::date BETWEEN y.start_date AND y.end_date ORDER BY y.start_date DESC LIMIT 1),
            (SELECT y.id FROM school_years y WHERE y.organization_id = f.organization_id AND y.status = 'active'))
    """)
    op.execute("""
        UPDATE answer_facts f SET term_code = t.code FROM school_terms t
         WHERE t.school_year_id = f.school_year_id AND f.created_at::date BETWEEN t.start_date AND t.end_date
    """)
    op.execute("""
        UPDATE answer_facts f SET class_ids = COALESCE((
            SELECT array_agg(cm.class_id) FROM class_members cm JOIN classes c ON c.id = cm.class_id
             WHERE cm.user_id = f.student_id AND c.school_year_id = f.school_year_id), '{}')
    """)


def downgrade() -> None:
    op.drop_index("ix_answer_facts_class_ids", table_name="answer_facts")
    for col in ("class_ids", "term_code", "school_year_id"):
        op.drop_column("answer_facts", col)
    for col in ("left_at", "joined_at", "status"):
        op.drop_column("class_members", col)
