"""classes and members

Revision ID: 0003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "classes",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("grade", sa.SmallInteger()),
        sa.Column("school_year", sa.String(9), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "name", "school_year", name="uq_classes_org_name_year"),
    )
    op.create_table(
        "class_members",
        sa.Column("class_id", pg.UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True),
    )


def downgrade() -> None:
    op.drop_table("class_members")
    op.drop_table("classes")
