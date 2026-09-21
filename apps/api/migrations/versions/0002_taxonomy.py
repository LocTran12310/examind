"""taxonomy: subjects, grades, semesters, topics (ltree), tags

Revision ID: 0002
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _org():
    return sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True)


def upgrade() -> None:
    op.create_table(
        "subjects",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _org(),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("organization_id", "code"),
    )
    op.create_table(
        "grades",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _org(),
        sa.Column("level", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.UniqueConstraint("organization_id", "level"),
    )
    op.create_table(
        "semesters",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _org(),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("organization_id", "code"),
    )
    op.create_table(
        "topics",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _org(),
        sa.Column("subject_id", pg.UUID(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=False, index=True),
        sa.Column("parent_id", pg.UUID(as_uuid=True), sa.ForeignKey("topics.id"), index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("level_kind", sa.String(16), nullable=False),
        sa.Column("grade", sa.SmallInteger()),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("level_kind in ('strand','topic','subtopic','type')", name="ck_topics_level_kind"),
    )
    op.execute("ALTER TABLE topics ALTER COLUMN path TYPE ltree USING path::ltree")
    op.execute("CREATE INDEX ix_topics_path ON topics USING gist (path)")
    op.execute("CREATE UNIQUE INDEX uq_topics_org_path ON topics (organization_id, path)")
    op.create_table(
        "tags",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _org(),
        sa.Column("group", sa.String(16), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("\"group\" in ('method','skill','source','custom')", name="ck_tags_group"),
    )
    op.execute('CREATE UNIQUE INDEX uq_tags_org_group_name ON tags (organization_id, "group", lower(name))')


def downgrade() -> None:
    for t in ("tags", "topics", "semesters", "grades", "subjects"):
        op.drop_table(t)
