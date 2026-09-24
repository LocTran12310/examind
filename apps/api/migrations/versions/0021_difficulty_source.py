"""where a question's difficulty came from (difficulty-at-upload ADR-01)

`questions.difficulty` is about to be filled by machines — a position rule and a model — so a number a teacher
chose and a number a model guessed stop being distinguishable the moment the pipeline writes one. The column
records which: `auto` (the position rule), `ai` (the model), `manual` (a person). It is the same concept
`question_topics.source` already carries for a placement, now for a scalar field.

Nullable on purpose: every row written before this revision keeps NULL. A backfill would have to invent a
provenance for 376 empty levels and 2 a teacher set, and a wrong trace is worse than an absent one — the empty
ones are filled later by the backfill command, which writes its own source.

Revision ID: 0021
"""
from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("difficulty_source", sa.String(8)))


def downgrade() -> None:
    op.drop_column("questions", "difficulty_source")
