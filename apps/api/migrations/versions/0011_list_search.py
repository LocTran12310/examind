"""Accent-insensitive column search for data tables (ui-shadcn-shell ADR-03).

Revision ID: 0011
"""
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    # unaccent() is STABLE; an IMMUTABLE wrapper with an explicit dictionary can back an index.
    op.execute("""
        CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text
        LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
        AS $$ SELECT lower(public.unaccent('public.unaccent'::regdictionary, $1)) $$
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_full_name_trgm ON users USING gin (f_unaccent(full_name) gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_username_trgm ON users USING gin (f_unaccent(username) gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email_trgm ON users USING gin (f_unaccent(email) gin_trgm_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_email_trgm")
    op.execute("DROP INDEX IF EXISTS ix_users_username_trgm")
    op.execute("DROP INDEX IF EXISTS ix_users_full_name_trgm")
    op.execute("DROP FUNCTION IF EXISTS f_unaccent(text)")
