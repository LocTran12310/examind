"""An answer carries its own timing, and the fact it produces its attempt number (learning-telemetry ADR-01).

Existing answers keep zero seconds and no timestamps; existing facts keep nulls — nothing is backfilled because the
time a past answer took was never measured.

Revision ID: 0017
"""
from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("attempt_answers", sa.Column("first_seen_at", sa.DateTime(timezone=True)))
    op.add_column("attempt_answers", sa.Column("answered_at", sa.DateTime(timezone=True)))
    op.add_column("attempt_answers", sa.Column("seconds_spent", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("attempt_answers", sa.Column("save_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("answer_facts", sa.Column("seconds_spent", sa.Integer()))
    op.add_column("answer_facts", sa.Column("answered_at", sa.DateTime(timezone=True)))
    op.add_column("answer_facts", sa.Column("first_attempt", sa.Boolean()))


def downgrade() -> None:
    for column in ("first_attempt", "answered_at", "seconds_spent"):
        op.drop_column("answer_facts", column)
    for column in ("save_count", "seconds_spent", "answered_at", "first_seen_at"):
        op.drop_column("attempt_answers", column)
