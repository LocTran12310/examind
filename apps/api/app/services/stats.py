"""Reports over answer_facts (US-05, US-06, ADR-01, A-09, A-10)."""
from datetime import datetime
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.errors import forbidden
from app.deps import OrgScope
from app.models import Attempt, AttemptAnswer, Exam, ExamQuestion, Question, User
from app.services import assignments as assignment_service
from app.services.scoring import scaled


def _where(scope: OrgScope, alias: str, class_id=None, student_id=None, assignment_id=None, date_from=None, date_to=None,
           school_year_id=None, term_code=None):
    """SQL fragment + params restricting answer_facts; students only ever see their own facts."""
    parts, params = [f"{alias}.organization_id = :org"], {"org": scope.org_id}
    if scope.role == "student":
        student_id = scope.user.id
    elif scope.role not in ("org_admin", "teacher"):
        raise forbidden()
    if student_id:
        parts.append(f"{alias}.student_id = :student")
        params["student"] = uuid.UUID(str(student_id))
    if class_id:  # the class the student was in when answering, not the current one (school-years ADR-02)
        parts.append(f"cast(:klass as uuid) = any({alias}.class_ids)")
        params["klass"] = uuid.UUID(str(class_id))
    if school_year_id:
        parts.append(f"{alias}.school_year_id = :year")
        params["year"] = uuid.UUID(str(school_year_id))
    if term_code:
        parts.append(f"{alias}.term_code = :term")
        params["term"] = term_code
    if assignment_id:
        parts.append(f"{alias}.assignment_id = :assignment")
        params["assignment"] = uuid.UUID(str(assignment_id))
    if date_from:
        parts.append(f"{alias}.created_at >= :dfrom")
        params["dfrom"] = date_from
    if date_to:
        parts.append(f"{alias}.created_at < :dto")
        params["dto"] = date_to
    return " and ".join(parts), params


def topics(db: Session, scope: OrgScope, subject_id=None, **filters) -> list[dict]:
    where, params = _where(scope, "f", **filters)
    subject = ""
    if subject_id:
        subject = "and t.subject_id = :subject"
        params["subject"] = uuid.UUID(str(subject_id))
    rows = db.execute(text(f"""
        select t.id, t.parent_id, t.name, t.path::text as path, nlevel(t.path) as depth, t.level_kind,
               coalesce(sum(f.points), 0) as points, coalesce(sum(f.max_points), 0) as max_points, count(f.id) as answered
          from topics t
          join answer_facts f on f.topic_path <@ t.path and {where}
         where t.organization_id = :org {subject}
         group by t.id order by t.path"""), params).mappings().all()
    out = [{**dict(r), "ratio": round(r["points"] / r["max_points"], 4) if r["max_points"] else None} for r in rows]
    unc = db.execute(text(f"""select coalesce(sum(points),0) p, coalesce(sum(max_points),0) m, count(*) n
                              from answer_facts f where {where} and f.topic_path is null"""), params).mappings().one()
    if unc["n"]:
        out.append({"id": None, "parent_id": None, "name": "Chưa phân loại", "path": "", "depth": 1, "level_kind": "strand",
                    "points": unc["p"], "max_points": unc["m"], "answered": unc["n"], "ratio": round(unc["p"] / unc["m"], 4) if unc["m"] else None})
    return out


GROUP_SQL = {
    "type": "select f.qtype as key, f.qtype as label, sum(f.points) p, sum(f.max_points) m, count(*) n from answer_facts f where {w} group by f.qtype",
    "difficulty": "select coalesce(f.difficulty,'') as key, coalesce(f.difficulty,'') as label, sum(f.points) p, sum(f.max_points) m, count(*) n "
                  "from answer_facts f where {w} group by f.difficulty",
    "tag": "select t.id::text as key, t.name as label, sum(f.points) p, sum(f.max_points) m, count(*) n "
           "from answer_facts f join tags t on t.id = any(f.tag_ids) where {w} group by t.id, t.name",
}


def groups(db: Session, scope: OrgScope, by: str, **filters) -> list[dict]:
    if by not in GROUP_SQL:
        from app.core.errors import validation

        raise validation("Nhóm không hợp lệ", "by")
    where, params = _where(scope, "f", **filters)
    rows = db.execute(text(GROUP_SQL[by].format(w=where)), params).mappings().all()
    return sorted(({"key": r["key"], "label": r["label"], "points": r["p"], "max_points": r["m"], "answered": r["n"],
                    "ratio": round(r["p"] / r["m"], 4) if r["m"] else None} for r in rows), key=lambda x: (x["ratio"] is None, x["ratio"]))


def heatmap(db: Session, scope: OrgScope, class_id, level: int = 1, subject_id=None, term_code=None) -> dict:
    if scope.role not in ("org_admin", "teacher"):
        raise forbidden()
    level = max(1, min(4, int(level)))
    where, params = _where(scope, "f", class_id=class_id, term_code=term_code)
    params["lvl"] = level
    subject = ""
    if subject_id:
        subject = "and t.subject_id = :subject"
        params["subject"] = uuid.UUID(str(subject_id))
    rows = db.execute(text(f"""
        select f.student_id, t.id as topic_id, t.name, t.path::text as path, sum(f.points) p, sum(f.max_points) m, count(*) n
          from answer_facts f
          join topics t on t.organization_id = f.organization_id and nlevel(t.path) = :lvl and f.topic_path <@ t.path
         where {where} {subject}
         group by f.student_id, t.id order by t.path"""), params).mappings().all()
    students = {u.id: u for u in db.query(User).filter(User.id.in_({r["student_id"] for r in rows} or {uuid.uuid4()}))}
    columns = list({r["topic_id"]: {"id": r["topic_id"], "name": r["name"], "path": r["path"]} for r in rows}.values())
    cells: dict = {}
    for r in rows:
        cells.setdefault(str(r["student_id"]), {})[str(r["topic_id"])] = {"ratio": round(r["p"] / r["m"], 4) if r["m"] else None, "answered": r["n"]}
    members = db.execute(text("select u.id, u.full_name, u.username from users u join class_members cm on cm.user_id = u.id "
                              "join organization_members om on om.user_id = u.id and om.organization_id = :org and om.is_active "
                              "where cm.class_id = :k and om.role = 'student' order by u.full_name"),
                         {"k": uuid.UUID(str(class_id)), "org": scope.org_id}).mappings().all()
    return {"columns": columns, "rows": [{"student_id": m["id"], "full_name": m["full_name"], "username": m["username"],
                                          "cells": cells.get(str(m["id"]), {})} for m in members]}


def assignment_report(db: Session, scope: OrgScope, aid) -> dict:
    a = assignment_service.get(db, scope, aid)
    exam = db.get(Exam, a.exam_id)
    scale_to = float((exam.settings or {}).get("scale_to", 10))
    targets = assignment_service.student_ids(db, a)
    attempts = db.query(Attempt).filter(Attempt.assignment_id == a.id).order_by(Attempt.started_at).all()
    by_student: dict = {}
    for t in attempts:
        by_student.setdefault(t.student_id, []).append(t)
    users = {u.id: u for u in db.query(User).filter(User.id.in_(targets | set(by_student) or {uuid.uuid4()}))}
    students, scores = [], []
    for sid in sorted(targets | set(by_student), key=lambda i: users[i].full_name if i in users else ""):
        ts = by_student.get(sid, [])
        best = max((t for t in ts if t.status == "submitted"), key=lambda t: t.score or 0, default=None)
        latest = ts[-1] if ts else None
        s10 = scaled(best.score or 0, best.max_score or 0, scale_to) if best else None
        if s10 is not None:
            scores.append(s10)
        u = users.get(sid)
        students.append({"student_id": sid, "full_name": u.full_name if u else "?", "username": u.username if u else "?",
                         "status": "submitted" if best else ("in_progress" if latest else "not_started"),
                         "attempt_id": (best or latest).id if (best or latest) else None, "score10": s10,
                         "needs_grading": bool(best and best.needs_grading), "tab_switches": max((t.tab_switches for t in ts), default=0)})
    buckets = [0] * 10
    for s in scores:
        buckets[min(9, int(s // (scale_to / 10)))] += 1
    submitted_ids = [t.id for t in attempts if t.status == "submitted"]
    per_question = []
    rows = db.query(ExamQuestion, Question).join(Question, Question.id == ExamQuestion.question_id).filter(ExamQuestion.exam_id == a.exam_id).order_by(ExamQuestion.position).all()
    answers: dict = {}
    if submitted_ids:
        for ans in db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id.in_(submitted_ids)):
            answers.setdefault(ans.question_id, []).append(ans)
    for eq, q in rows:
        got = answers.get(q.id, [])
        graded = [x for x in got if x.points is not None]
        wrong: dict = {}
        if q.type == "mcq":
            for x in got:
                k = (x.response or {}).get("key")
                if k and k != (x.key_snapshot or {}).get("key"):
                    wrong[k] = wrong.get(k, 0) + 1
        top_wrong = max(wrong.items(), key=lambda kv: kv[1]) if wrong else None
        per_question.append({"question_id": q.id, "position": eq.position, "type": q.type, "stem": q.stem[:300],
                             "answered": len(got), "ratio": round(sum(x.points for x in graded) / sum(x.max_points for x in graded), 4) if graded and sum(x.max_points for x in graded) else None,
                             "top_wrong": {"label": top_wrong[0], "count": top_wrong[1]} if top_wrong else None})
    return {"assignment_id": a.id, "title": a.title, "students": students, "submitted": len({t.student_id for t in attempts if t.status == "submitted"}),
            "total_students": len(targets), "average": round(sum(scores) / len(scores), 2) if scores else None,
            "distribution": [{"from": i * scale_to / 10, "to": (i + 1) * scale_to / 10, "count": c} for i, c in enumerate(buckets)],
            "questions": per_question}


def parse_date(v: str | None) -> datetime | None:
    return datetime.fromisoformat(v) if v else None
