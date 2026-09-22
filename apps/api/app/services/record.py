"""Hồ sơ học sinh: classes and results per school year (school-years US-04)."""
import uuid

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.errors import forbidden, not_found
from app.deps import OrgScope
from app.models import ClassMember, SchoolClass, SchoolYear, User
from app.services.membership import member_ids

STATUS_LABEL = {"active": "Đang học", "promoted": "Lên lớp", "retained": "Ở lại lớp", "transferred": "Chuyển đi", "graduated": "Tốt nghiệp"}


def record(db: Session, scope: OrgScope, student_id) -> dict:
    if scope.role not in ("org_admin", "teacher") and not (scope.role == "student" and scope.user.id == student_id):
        raise forbidden()
    if not member_ids(db, scope.org_id, {student_id}):
        raise not_found("Không tìm thấy học sinh")
    user = db.get(User, student_id)
    enrollments = db.execute(
        select(ClassMember, SchoolClass, SchoolYear).join(SchoolClass, SchoolClass.id == ClassMember.class_id)
        .outerjoin(SchoolYear, SchoolYear.id == SchoolClass.school_year_id)
        .where(ClassMember.user_id == student_id, SchoolClass.organization_id == scope.org_id)
        .order_by(SchoolYear.start_date.desc().nulls_last(), SchoolClass.name)).all()
    params = {"org": scope.org_id, "s": uuid.UUID(str(student_id))}
    per_year = db.execute(text("""
        select f.school_year_id as year_id, count(*) as answered, sum(f.points) as p, sum(f.max_points) as m,
               count(distinct f.attempt_id) as attempts
          from answer_facts f where f.organization_id = :org and f.student_id = :s group by f.school_year_id"""), params).mappings().all()
    per_term = db.execute(text("""
        select f.school_year_id as year_id, f.term_code as term, count(*) as answered, sum(f.points) as p, sum(f.max_points) as m
          from answer_facts f where f.organization_id = :org and f.student_id = :s and f.term_code is not null
         group by f.school_year_id, f.term_code"""), params).mappings().all()
    topics = db.execute(text("""
        select f.school_year_id as year_id, t.id as topic_id, t.name, sum(f.points) as p, sum(f.max_points) as m, count(*) as answered
          from answer_facts f
          join topics t on t.organization_id = f.organization_id and nlevel(t.path) = 1 and f.topic_path <@ t.path
         where f.organization_id = :org and f.student_id = :s
         group by f.school_year_id, t.id, t.name, t.path order by t.path"""), params).mappings().all()
    years: dict = {}
    for cm, c, y in enrollments:
        key = str(y.id) if y else "none"
        entry = years.setdefault(key, {"year": {"id": y.id, "code": y.code, "status": y.status} if y else None, "classes": [],
                                       "answered": 0, "ratio": None, "attempts": 0, "terms": {}, "topics": []})
        entry["classes"].append({"id": c.id, "name": c.name, "grade": c.grade, "status": cm.status, "status_label": STATUS_LABEL.get(cm.status, cm.status),
                                 "joined_at": cm.joined_at, "left_at": cm.left_at})
    known = {str(y.id): y for y in db.scalars(select(SchoolYear).where(SchoolYear.organization_id == scope.org_id))}
    for r in per_year:
        key = str(r["year_id"]) if r["year_id"] else "none"
        y = known.get(key)
        entry = years.setdefault(key, {"year": {"id": y.id, "code": y.code, "status": y.status} if y else None, "classes": [],
                                       "answered": 0, "ratio": None, "attempts": 0, "terms": {}, "topics": []})
        entry.update(answered=r["answered"], ratio=round(r["p"] / r["m"], 4) if r["m"] else None, attempts=r["attempts"])
    for r in per_term:
        key = str(r["year_id"]) if r["year_id"] else "none"
        if key in years:
            years[key]["terms"][r["term"]] = {"answered": r["answered"], "ratio": round(r["p"] / r["m"], 4) if r["m"] else None}
    for r in topics:
        key = str(r["year_id"]) if r["year_id"] else "none"
        if key in years:
            years[key]["topics"].append({"id": r["topic_id"], "name": r["name"], "answered": r["answered"],
                                         "ratio": round(r["p"] / r["m"], 4) if r["m"] else None})
    ordered = sorted(years.values(), key=lambda e: e["year"]["code"] if e["year"] else "", reverse=True)
    return {"student": {"id": user.id, "username": user.username, "full_name": user.full_name}, "years": ordered}

