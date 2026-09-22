"""Report reads of analytics: sums over answer_facts (assessment's table) by topic (taxonomy's tree), group and
student, and the class members a heatmap lists (academic / identity tables), in SQL (ADR-01)."""
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.analytics.application.dto import FactScope

GROUP_SQL = {
    "type": "select f.qtype as key, f.qtype as label, sum(f.points) p, sum(f.max_points) m, count(*) n from answer_facts f where {w} group by f.qtype",
    "difficulty": "select coalesce(f.difficulty,'') as key, coalesce(f.difficulty,'') as label, sum(f.points) p, sum(f.max_points) m, count(*) n "
                  "from answer_facts f where {w} group by f.difficulty",
    "tag": "select t.id::text as key, t.name as label, sum(f.points) p, sum(f.max_points) m, count(*) n "
           "from answer_facts f join tags t on t.id = any(f.tag_ids) where {w} group by t.id, t.name",
}


def _where(scope: FactScope, alias: str) -> tuple[str, dict]:
    """SQL fragment + params restricting answer_facts to the scope."""
    f = scope.filters
    parts, params = [f"{alias}.organization_id = :org"], {"org": scope.org_id}
    if f.student_id:
        parts.append(f"{alias}.student_id = :student")
        params["student"] = f.student_id
    if f.class_id:  # the class the student was in when answering, not the current one (school-years ADR-02)
        parts.append(f"cast(:klass as uuid) = any({alias}.class_ids)")
        params["klass"] = f.class_id
    if f.school_year_id:
        parts.append(f"{alias}.school_year_id = :year")
        params["year"] = f.school_year_id
    if f.term_code:
        parts.append(f"{alias}.term_code = :term")
        params["term"] = f.term_code
    if f.assignment_id:
        parts.append(f"{alias}.assignment_id = :assignment")
        params["assignment"] = f.assignment_id
    if f.date_from:
        parts.append(f"{alias}.created_at >= :dfrom")
        params["dfrom"] = f.date_from
    if f.date_to:
        parts.append(f"{alias}.created_at < :dto")
        params["dto"] = f.date_to
    return " and ".join(parts), params


def _subject(params: dict, subject_id: uuid.UUID | None) -> str:
    if not subject_id:
        return ""
    params["subject"] = subject_id
    return "and t.subject_id = :subject"


class SqlReportReader:
    def __init__(self, session: Session):
        self.session = session

    def topics(self, scope: FactScope, subject_id: uuid.UUID | None) -> list[dict]:
        where, params = _where(scope, "f")
        subject = _subject(params, subject_id)
        return [dict(r) for r in self.session.execute(text(f"""
            select t.id, t.parent_id, t.name, t.path::text as path, nlevel(t.path) as depth, t.level_kind,
                   coalesce(sum(f.points), 0) as points, coalesce(sum(f.max_points), 0) as max_points, count(f.id) as answered
              from topics t
              join answer_facts f on f.topic_path <@ t.path and {where}
             where t.organization_id = :org {subject}
             group by t.id order by t.path"""), params).mappings().all()]

    def unclassified(self, scope: FactScope) -> dict:
        where, params = _where(scope, "f")
        return dict(self.session.execute(text(f"""select coalesce(sum(points),0) p, coalesce(sum(max_points),0) m, count(*) n
                                                   from answer_facts f where {where} and f.topic_path is null"""), params).mappings().one())

    def groups(self, scope: FactScope, by: str) -> list[dict]:
        where, params = _where(scope, "f")
        return [dict(r) for r in self.session.execute(text(GROUP_SQL[by].format(w=where)), params).mappings().all()]

    def heat(self, scope: FactScope, level: int, subject_id: uuid.UUID | None) -> list[dict]:
        where, params = _where(scope, "f")
        params["lvl"] = level
        subject = _subject(params, subject_id)
        return [dict(r) for r in self.session.execute(text(f"""
            select f.student_id, t.id as topic_id, t.name, t.path::text as path, sum(f.points) p, sum(f.max_points) m, count(*) n
              from answer_facts f
              join topics t on t.organization_id = f.organization_id and nlevel(t.path) = :lvl and f.topic_path <@ t.path
             where {where} {subject}
             group by f.student_id, t.id order by t.path"""), params).mappings().all()]

    def class_students(self, org_id: uuid.UUID, class_id: uuid.UUID) -> list[dict]:
        return [dict(r) for r in self.session.execute(text(
            "select u.id, u.full_name, u.username from users u join class_members cm on cm.user_id = u.id "
            "join organization_members om on om.user_id = u.id and om.organization_id = :org and om.is_active "
            "where cm.class_id = :k and om.role = 'student' order by u.full_name"), {"k": class_id, "org": org_id}).mappings().all()]
