"""A review event knows which request wrote it, so a bulk edit is one unit (bulk-safety ADR-01).

Rows written before this revision keep `batch_id` NULL and are read as one event that cannot be taken back: a batch
cannot be reconstructed from a timestamp with any confidence, so nothing is backfilled.

Revision ID: 0019
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("review_events", sa.Column("batch_id", UUID(as_uuid=True)))
    # one batch of the org (the history list, the undo), and the org's events newest first (the same list, unfiltered)
    op.create_index("ix_review_events_org_batch", "review_events", ["organization_id", "batch_id"])
    op.create_index("ix_review_events_org_created", "review_events", ["organization_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_review_events_org_created", table_name="review_events")
    op.drop_index("ix_review_events_org_batch", table_name="review_events")
    op.drop_column("review_events", "batch_id")
