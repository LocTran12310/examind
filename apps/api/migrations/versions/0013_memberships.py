"""Users in several organisations: organization_members + users.last_org_id (school-structure-multi-org ADR-02).

Revision ID: 0013
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_members",
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True, index=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_organization_members_org_role", "organization_members", ["organization_id", "role"])
    op.add_column("users", sa.Column("last_org_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL")))
    op.execute("INSERT INTO organization_members (user_id, organization_id, role, is_active, created_at) "
               "SELECT id, organization_id, role, true, created_at FROM users ON CONFLICT DO NOTHING")


def downgrade() -> None:
    op.drop_column("users", "last_org_id")
    op.drop_index("ix_organization_members_org_role", table_name="organization_members")
    op.drop_table("organization_members")
