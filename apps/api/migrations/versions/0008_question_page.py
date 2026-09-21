"""question source page (for the review queue's page view)

Revision ID: 0008
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("page", sa.Integer()))


def downgrade() -> None:
    op.drop_column("questions", "page")
