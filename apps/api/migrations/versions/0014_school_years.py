"""School years with HK1/HK2 terms; classes point at their year (school-years ADR-01).

Revision ID: 0014
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "school_years",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("code", sa.String(9), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="planning"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_school_years_org_code"),
        sa.CheckConstraint("start_date < end_date", name="ck_school_years_dates"),
    )
    op.create_index("uq_school_years_one_active", "school_years", ["organization_id"], unique=True, postgresql_where=sa.text("status = 'active'"))
    op.create_table(
        "school_terms",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("school_year_id", pg.UUID(as_uuid=True), sa.ForeignKey("school_years.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("code", sa.String(8), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.UniqueConstraint("school_year_id", "code", name="uq_school_terms_year_code"),
    )
    op.add_column("classes", sa.Column("school_year_id", pg.UUID(as_uuid=True), sa.ForeignKey("school_years.id"), index=True))

    # Backfill: one year per distinct class year string (plus the current year for every tenant org).
    op.execute("""
        WITH cur AS (SELECT CASE WHEN extract(month FROM now()) >= 8 THEN extract(year FROM now())::int
                                 ELSE extract(year FROM now())::int - 1 END AS y),
        codes AS (
            SELECT DISTINCT organization_id, school_year AS code FROM classes WHERE school_year ~ '^\\d{4}-\\d{4}$'
            UNION SELECT o.id, (cur.y || '-' || (cur.y + 1)) FROM organizations o, cur WHERE NOT o.is_system
        )
        INSERT INTO school_years (id, organization_id, code, name, start_date, end_date, status)
        SELECT gen_random_uuid(), c.organization_id, c.code, 'Năm học ' || c.code,
               make_date(split_part(c.code, '-', 1)::int, 9, 5), make_date(split_part(c.code, '-', 2)::int, 5, 31),
               CASE WHEN c.code = (cur.y || '-' || (cur.y + 1)) THEN 'active'
                    WHEN split_part(c.code, '-', 1)::int < cur.y THEN 'closed' ELSE 'planning' END
          FROM codes c, cur
    """)
    op.execute("""
        INSERT INTO school_terms (id, school_year_id, code, name, start_date, end_date)
        SELECT gen_random_uuid(), y.id, t.code, t.name,
               CASE t.code WHEN 'hk1' THEN y.start_date ELSE make_date(extract(year FROM y.end_date)::int, 1, 16) END,
               CASE t.code WHEN 'hk1' THEN make_date(extract(year FROM y.end_date)::int, 1, 15) ELSE y.end_date END
          FROM school_years y CROSS JOIN (VALUES ('hk1', 'Học kỳ 1'), ('hk2', 'Học kỳ 2')) AS t(code, name)
    """)
    op.execute("""
        UPDATE classes c SET school_year_id = y.id FROM school_years y
         WHERE y.organization_id = c.organization_id AND y.code = c.school_year
    """)


def downgrade() -> None:
    op.drop_column("classes", "school_year_id")
    op.drop_table("school_terms")
    op.drop_index("uq_school_years_one_active", table_name="school_years")
    op.drop_table("school_years")
