"""School structure: levels (Cấp học) › grades (Khối) › classes (school-structure-multi-org ADR-01).

Revision ID: 0012
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

DEFAULT_LEVELS = [("thcs", "Trung học cơ sở", 6, 9, 0), ("thpt", "Trung học phổ thông", 10, 12, 1)]


def upgrade() -> None:
    op.create_table(
        "school_levels",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("grade_from", sa.SmallInteger(), nullable=False),
        sa.Column("grade_to", sa.SmallInteger(), nullable=False),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_school_levels_org_code"),
        sa.CheckConstraint("grade_from <= grade_to", name="ck_school_levels_range"),
    )
    op.add_column("grades", sa.Column("school_level_id", pg.UUID(as_uuid=True), sa.ForeignKey("school_levels.id"), index=True))
    op.add_column("classes", sa.Column("grade_id", pg.UUID(as_uuid=True), sa.ForeignKey("grades.id"), index=True))

    # Backfill: every org gets THCS/THPT; grades attach to the level containing them; classes to their grade.
    for code, name, lo, hi, sort in DEFAULT_LEVELS:
        op.execute(sa.text(
            "INSERT INTO school_levels (id, organization_id, code, name, grade_from, grade_to, sort) "
            "SELECT gen_random_uuid(), o.id, :code, :name, :lo, :hi, :sort FROM organizations o "
            "WHERE NOT EXISTS (SELECT 1 FROM school_levels l WHERE l.organization_id = o.id AND l.code = :code)"
        ).bindparams(code=code, name=name, lo=lo, hi=hi, sort=sort))
    op.execute("""
        UPDATE grades g SET school_level_id = l.id FROM school_levels l
         WHERE l.organization_id = g.organization_id AND g.level BETWEEN l.grade_from AND l.grade_to AND g.school_level_id IS NULL
    """)
    # grades that exist on classes but not in the taxonomy (e.g. khối 5) get a row under the nearest level
    op.execute("""
        INSERT INTO grades (id, organization_id, level, name, school_level_id)
        SELECT DISTINCT ON (c.organization_id, c.grade) gen_random_uuid(), c.organization_id, c.grade, 'Lớp ' || c.grade,
               (SELECT l.id FROM school_levels l WHERE l.organization_id = c.organization_id
                 ORDER BY (c.grade BETWEEN l.grade_from AND l.grade_to) DESC, abs(c.grade - l.grade_from) LIMIT 1)
          FROM classes c
         WHERE c.grade IS NOT NULL
           AND NOT EXISTS (SELECT 1 FROM grades g WHERE g.organization_id = c.organization_id AND g.level = c.grade)
    """)
    op.execute("""
        UPDATE classes c SET grade_id = g.id FROM grades g
         WHERE g.organization_id = c.organization_id AND g.level = c.grade AND c.grade_id IS NULL
    """)


def downgrade() -> None:
    op.drop_column("classes", "grade_id")
    op.drop_column("grades", "school_level_id")
    op.drop_table("school_levels")
