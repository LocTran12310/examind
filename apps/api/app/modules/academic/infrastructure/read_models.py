import uuid

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.modules.academic.application.dto import (
    ClassView, GradeView, LevelView, MemberView, RosterEntry, YearView, class_view, grade_view, level_view, year_view,
)
from app.modules.academic.domain.entities import Grade, SchoolClass, SchoolLevel, SchoolYear
from app.modules.academic.infrastructure import orm  # noqa: F401  (mapping)
from app.shared.application.search import Page, SearchRequest
from app.shared.infrastructure.schema.academic import class_members, classes, school_years
from app.shared.infrastructure.schema.identity import organizations, users
from app.shared.infrastructure.schema.taxonomy import grades, school_levels
from app.shared.infrastructure.sql_search import Col, search

YEAR_CLASS_COUNT = select(func.count(classes.c.id)).where(classes.c.school_year_id == school_years.c.id).correlate(school_years).scalar_subquery()
YEAR_COLS = {"code": Col(school_years.c.code), "name": Col(school_years.c.name), "status": Col(school_years.c.status, "exact"),
             "start_date": Col(school_years.c.start_date, "day"), "class_count": Col(YEAR_CLASS_COUNT, filterable=False)}

MEMBER_COUNT = func.count(class_members.c.user_id)
CLASS_COLS = {
    "name": Col(classes.c.name),
    "grade": Col(classes.c.grade, "number"),
    "grade_id": Col(classes.c.grade_id, "uuid"),
    "school_year": Col(classes.c.school_year, "exact"),
    "school_year_id": Col(classes.c.school_year_id, "uuid"),
    "member_count": Col(MEMBER_COUNT, filterable=False),
    "created_at": Col(classes.c.created_at, "date"),
}

LEVEL_GRADE_COUNT = select(func.count(grades.c.id)).where(grades.c.school_level_id == school_levels.c.id).correlate(school_levels).scalar_subquery()
LEVEL_COLS = {"code": Col(school_levels.c.code), "name": Col(school_levels.c.name), "sort": Col(school_levels.c.sort, "number"),
              "grade_count": Col(LEVEL_GRADE_COUNT, filterable=False)}

GRADE_CLASS_COUNT = select(func.count(classes.c.id)).where(classes.c.grade_id == grades.c.id).correlate(grades).scalar_subquery()
GRADE_COLS = {"level": Col(grades.c.level, "number"), "name": Col(grades.c.name), "school_level_id": Col(grades.c.school_level_id, "uuid"),
              "class_count": Col(GRADE_CLASS_COUNT, filterable=False)}


class SqlYearReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID, req: SearchRequest) -> Page[YearView]:
        stmt = select(SchoolYear, YEAR_CLASS_COUNT).where(school_years.c.organization_id == org_id)
        rows, total = search(self.session, stmt, req, YEAR_COLS, text=[school_years.c.code, school_years.c.name], scalars=False,
                             default_sort=[school_years.c.start_date.desc()])
        return Page([year_view(y, n) for y, n in rows], total, req.page, req.limit)


class SqlClassReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID, req: SearchRequest, school_year_id: uuid.UUID | None = None,
               grade_id: uuid.UUID | None = None) -> Page[ClassView]:
        stmt = (select(SchoolClass, MEMBER_COUNT).outerjoin(class_members, class_members.c.class_id == classes.c.id)
                .where(classes.c.organization_id == org_id).group_by(classes.c.id))
        if school_year_id:
            stmt = stmt.where(classes.c.school_year_id == school_year_id)
        if grade_id:
            stmt = stmt.where(classes.c.grade_id == grade_id)
        rows, total = search(self.session, stmt, req, CLASS_COLS, text=[classes.c.name], scalars=False,
                             default_sort=[classes.c.school_year.desc(), classes.c.name])
        return Page([class_view(c, n) for c, n in rows], total, req.page, req.limit)

    def members(self, class_id: uuid.UUID) -> list[MemberView]:
        u = users.c
        rows = self.session.execute(
            select(u.id, u.username, u.full_name, u.email, u.role, u.is_active, u.must_change_password, u.last_login_at, u.created_at,
                   organizations.c.code).join(class_members, class_members.c.user_id == u.id)
            .join(organizations, organizations.c.id == u.organization_id)
            .where(class_members.c.class_id == class_id).order_by(u.full_name)).all()
        return [MemberView(*r) for r in rows]

    def roster(self, class_id: uuid.UUID) -> list[RosterEntry]:
        rows = self.session.execute(
            select(users.c.id, users.c.full_name, users.c.username, class_members.c.status).join(class_members, class_members.c.user_id == users.c.id)
            .where(class_members.c.class_id == class_id).order_by(users.c.full_name)).all()
        return [RosterEntry(*r) for r in rows]


class SqlLevelReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID, req: SearchRequest) -> Page[LevelView]:
        stmt = select(SchoolLevel, LEVEL_GRADE_COUNT).where(school_levels.c.organization_id == org_id)
        rows, total = search(self.session, stmt, req, LEVEL_COLS, text=[school_levels.c.name, school_levels.c.code], scalars=False,
                             default_sort=[school_levels.c.sort, school_levels.c.grade_from])
        return Page([level_view(lv, n) for lv, n in rows], total, req.page, req.limit)


class SqlGradeReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID, req: SearchRequest, school_level_id: uuid.UUID | None = None) -> Page[GradeView]:
        stmt = select(Grade, GRADE_CLASS_COUNT).where(grades.c.organization_id == org_id)
        if school_level_id:
            stmt = stmt.where(grades.c.school_level_id == school_level_id)
        rows, total = search(self.session, stmt, req, GRADE_COLS, text=[grades.c.name], scalars=False, default_sort=[grades.c.level])
        return Page([grade_view(g, n) for g, n in rows], total, req.page, req.limit)


class SqlStructureReader:
    def __init__(self, session: Session):
        self.session = session

    def tree(self, org_id: uuid.UUID, school_year: str | None = None, school_year_id: uuid.UUID | None = None) -> dict:
        db = self.session
        members = select(class_members.c.class_id, func.count().label("n")).group_by(class_members.c.class_id).subquery()
        cstmt = (select(classes.c.id, classes.c.name, classes.c.school_year, classes.c.grade_id, func.coalesce(members.c.n, 0).label("n"))
                 .outerjoin(members, members.c.class_id == classes.c.id).where(classes.c.organization_id == org_id).order_by(classes.c.name))
        if school_year:
            cstmt = cstmt.where(classes.c.school_year == school_year)
        if school_year_id:
            cstmt = cstmt.where(classes.c.school_year_id == school_year_id)
        by_grade: dict = {}
        for c in db.execute(cstmt):
            by_grade.setdefault(c.grade_id, []).append({"id": c.id, "name": c.name, "school_year": c.school_year, "member_count": c.n})
        grades_by_level: dict = {}
        for g in db.execute(select(grades).where(grades.c.organization_id == org_id).order_by(grades.c.level)):
            cls = by_grade.get(g.id, [])
            grades_by_level.setdefault(g.school_level_id, []).append(
                {"id": g.id, "level": g.level, "name": g.name, "class_count": len(cls), "student_count": sum(c["member_count"] for c in cls), "classes": cls})
        levels = []
        for lv in db.execute(select(school_levels).where(school_levels.c.organization_id == org_id)
                             .order_by(school_levels.c.sort, school_levels.c.grade_from)):
            gs = grades_by_level.get(lv.id, [])
            levels.append({"id": lv.id, "code": lv.code, "name": lv.name, "grade_from": lv.grade_from, "grade_to": lv.grade_to,
                           "class_count": sum(g["class_count"] for g in gs), "student_count": sum(g["student_count"] for g in gs), "grades": gs})
        return {"levels": levels, "unassigned": by_grade.get(None, [])}


ENROLLMENT_LABEL = {"active": "Đang học", "promoted": "Lên lớp", "retained": "Ở lại lớp", "transferred": "Chuyển đi", "graduated": "Tốt nghiệp"}


def _ratio(p, m):
    return round(p / m, 4) if m else None


class SqlRecordReader:
    """Hồ sơ học sinh: classes per year from the memberships, results per year / term / top-level topic from answer facts."""

    def __init__(self, session: Session):
        self.session = session

    def record(self, org_id: uuid.UUID, student_id: uuid.UUID) -> dict:
        db = self.session
        user = db.execute(select(users.c.id, users.c.username, users.c.full_name).where(users.c.id == student_id)).one()
        y = school_years.c
        enrollments = db.execute(
            select(class_members.c.status, class_members.c.joined_at, class_members.c.left_at, classes.c.id, classes.c.name, classes.c.grade,
                   y.id.label("year_id"), y.code.label("year_code"), y.status.label("year_status"))
            .join(classes, classes.c.id == class_members.c.class_id).outerjoin(school_years, y.id == classes.c.school_year_id)
            .where(class_members.c.user_id == student_id, classes.c.organization_id == org_id)
            .order_by(y.start_date.desc().nulls_last(), classes.c.name)).all()
        params = {"org": org_id, "s": uuid.UUID(str(student_id))}
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

        def entry(year):
            return {"year": year, "classes": [], "answered": 0, "ratio": None, "attempts": 0, "terms": {}, "topics": []}

        years: dict = {}
        for r in enrollments:
            key = str(r.year_id) if r.year_id else "none"
            e = years.setdefault(key, entry({"id": r.year_id, "code": r.year_code, "status": r.year_status} if r.year_id else None))
            e["classes"].append({"id": r.id, "name": r.name, "grade": r.grade, "status": r.status,
                                 "status_label": ENROLLMENT_LABEL.get(r.status, r.status), "joined_at": r.joined_at, "left_at": r.left_at})
        known = {str(k.id): k for k in db.execute(select(y.id, y.code, y.status).where(y.organization_id == org_id))}
        for r in per_year:
            key = str(r["year_id"]) if r["year_id"] else "none"
            k = known.get(key)
            e = years.setdefault(key, entry({"id": k.id, "code": k.code, "status": k.status} if k else None))
            e.update(answered=r["answered"], ratio=_ratio(r["p"], r["m"]), attempts=r["attempts"])
        for r in per_term:
            key = str(r["year_id"]) if r["year_id"] else "none"
            if key in years:
                years[key]["terms"][r["term"]] = {"answered": r["answered"], "ratio": _ratio(r["p"], r["m"])}
        for r in topics:
            key = str(r["year_id"]) if r["year_id"] else "none"
            if key in years:
                years[key]["topics"].append({"id": r["topic_id"], "name": r["name"], "answered": r["answered"], "ratio": _ratio(r["p"], r["m"])})
        ordered = sorted(years.values(), key=lambda e: e["year"]["code"] if e["year"] else "", reverse=True)
        return {"student": {"id": user.id, "username": user.username, "full_name": user.full_name}, "years": ordered}
