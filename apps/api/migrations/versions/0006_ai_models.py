"""ai_models registry

Revision ID: 0006
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_models",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(16), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("base_url", sa.String(300)),
        sa.Column("api_key_enc", sa.Text()),
        sa.Column("capabilities", pg.ARRAY(sa.String(16)), nullable=False, server_default="{text}"),
        sa.Column("is_free", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("provider in ('ollama','openai','anthropic')", name="ck_ai_models_provider"),
    )


def downgrade() -> None:
    op.drop_table("ai_models")
