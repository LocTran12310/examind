"""exams, assignments, attempts, answers, answer_facts

Revision ID: 0009
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def _id():
    return sa.Column("id", pg.UUID(as_uuid=True), primary_key=True)


def _org():
    return sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True)


def _created():
    return sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "exams", _id(), _org(),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("subject_id", pg.UUID(as_uuid=True), sa.ForeignKey("subjects.id")),
        sa.Column("grade", sa.SmallInteger()),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("settings", pg.JSONB(), nullable=False, server_default="{}"),
        sa.Column("blueprint", pg.JSONB(), nullable=False, server_default="[]"),
        sa.Column("source", sa.String(16), nullable=False, server_default="manual"),
        sa.Column("created_by", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        _created(),
    )
    op.create_table(
        "exam_questions",
        sa.Column("exam_id", pg.UUID(as_uuid=True), sa.ForeignKey("exams.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("question_id", pg.UUID(as_uuid=True), sa.ForeignKey("questions.id"), primary_key=True, index=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(8), nullable=False, server_default="I"),
        sa.Column("points", sa.Float(), nullable=False),
        sa.Column("row", sa.Integer()),
    )
    op.create_table(
        "assignments", _id(), _org(),
        sa.Column("exam_id", pg.UUID(as_uuid=True), sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("open_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("shuffle_questions", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("shuffle_options", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("results_policy", sa.String(16), nullable=False, server_default="after_submit"),
        sa.Column("created_by", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        _created(),
        sa.CheckConstraint("close_at > open_at", name="ck_assignments_window"),
        sa.CheckConstraint("results_policy in ('after_submit','after_close','never')", name="ck_assignments_policy"),
    )
    op.create_table(
        "assignment_targets", _id(),
        sa.Column("assignment_id", pg.UUID(as_uuid=True), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("class_id", pg.UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE")),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.CheckConstraint("(class_id is null) <> (user_id is null)", name="ck_targets_one"),
    )
    op.create_table(
        "attempts", _id(), _org(),
        sa.Column("assignment_id", pg.UUID(as_uuid=True), sa.ForeignKey("assignments.id", ondelete="CASCADE"), index=True),
        sa.Column("exam_id", pg.UUID(as_uuid=True), sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("student_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(16), nullable=False, server_default="in_progress"),
        sa.Column("score", sa.Float()),
        sa.Column("max_score", sa.Float()),
        sa.Column("needs_grading", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("question_order", pg.JSONB(), nullable=False, server_default="[]"),
        sa.Column("option_orders", pg.JSONB(), nullable=False, server_default="{}"),
        sa.Column("tab_switches", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_attempts_open", "attempts", ["status", "deadline_at"])
    op.create_table(
        "attempt_answers",
        sa.Column("attempt_id", pg.UUID(as_uuid=True), sa.ForeignKey("attempts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("question_id", pg.UUID(as_uuid=True), sa.ForeignKey("questions.id"), primary_key=True),
        sa.Column("response", pg.JSONB()),
        sa.Column("is_correct", sa.Boolean()),
        sa.Column("points", sa.Float()),
        sa.Column("max_points", sa.Float(), nullable=False, server_default="0"),
        sa.Column("key_snapshot", pg.JSONB()),
        sa.Column("comment", sa.Text()),
        sa.Column("graded_by", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "answer_facts", _id(), _org(),
        sa.Column("attempt_id", pg.UUID(as_uuid=True), sa.ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("assignment_id", pg.UUID(as_uuid=True), index=True),
        sa.Column("exam_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", pg.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("question_id", pg.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("topic_path", sa.Text()),
        sa.Column("tag_ids", pg.ARRAY(pg.UUID(as_uuid=True)), nullable=False, server_default="{}"),
        sa.Column("qtype", sa.String(16), nullable=False),
        sa.Column("difficulty", sa.String(8)),
        sa.Column("points", sa.Float(), nullable=False),
        sa.Column("max_points", sa.Float(), nullable=False),
        sa.Column("correct_ratio", sa.Float(), nullable=False),
        _created(),
    )
    op.execute("ALTER TABLE answer_facts ALTER COLUMN topic_path TYPE ltree USING topic_path::ltree")
    op.execute("CREATE INDEX ix_answer_facts_topic ON answer_facts USING gist (topic_path)")
    op.execute("CREATE INDEX ix_answer_facts_tags ON answer_facts USING gin (tag_ids)")


def downgrade() -> None:
    for t in ("answer_facts", "attempt_answers", "attempts", "assignment_targets", "assignments", "exam_questions", "exams"):
        op.drop_table(t)
