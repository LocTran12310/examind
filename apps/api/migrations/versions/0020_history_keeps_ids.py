"""A review event keeps the id of its question after the question is deleted (history-keeps-ids ADR-01).

`review_events.question_id` carried `ON DELETE SET NULL`, so deleting a question emptied the link in every event
it had ever left behind: the rows survived with their before/after snapshots and no longer said whose. Dropping
the constraint keeps the column, its type and its index, and leaves a deletion touching no row of the history.

The upgrade loses nothing and backfills nothing — the ids nulled before this revision are not in the database any
more and cannot be recovered.

**The downgrade does lose data** (ADR-02): a foreign key can only be created when every value in the column
exists in `questions`, so it first nulls the ids of questions that are gone — exactly the ids this revision
exists to keep.

Revision ID: 0020
"""
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("review_events_question_id_fkey", "review_events", type_="foreignkey")


def downgrade() -> None:
    op.execute("""update review_events set question_id = null
                   where question_id is not null
                     and not exists (select 1 from questions q where q.id = review_events.question_id)""")
    op.create_foreign_key("review_events_question_id_fkey", "review_events", "questions",
                          ["question_id"], ["id"], ondelete="SET NULL")
