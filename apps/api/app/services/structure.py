"""School structure: Cấp học › Khối › Lớp (school-structure-multi-org ADR-01, A-01…A-04)."""
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, conflict, forbidden, not_found, validation
from app.deps import OrgScope
from app.models import ClassMember, Grade, SchoolClass, SchoolLevel
from app.services import audit
from app.services.paging import Col, ListParams, paginate

CODE_RE = re.compile(r"^[a-z0-9_-]{1,20}$")


def _admin(scope: OrgScope) -> None:
    if scope.role != "org_admin":
        raise forbidden()


def in_use(message: str) -> AppError:
    return AppError("in_use", message, 409)


# ------------------------------------------------------------------ levels

GRADE_COUNT = select(func.count(Grade.id)).where(Grade.school_level_id == SchoolLevel.id).correlate(SchoolLevel).scalar_subquery()
LEVEL_COLS = {"code": Col(SchoolLevel.code), "name": Col(SchoolLevel.name), "sort": Col(SchoolLevel.sort, "number"),
              "grade_count": Col(GRADE_COUNT, filterable=False)}


def get_level(db: Session, scope: OrgScope, level_id) -> SchoolLevel:
    lv = db.get(SchoolLevel, level_id)
    if lv is None or lv.organization_id != scope.org_id:
        raise not_found("Không tìm thấy cấp học")
    return lv


def list_levels(db: Session, scope: OrgScope, params: ListParams):
    stmt = select(SchoolLevel, GRADE_COUNT).where(SchoolLevel.organization_id == scope.org_id)
    return paginate(db, stmt, params, LEVEL_COLS, search=[SchoolLevel.name, SchoolLevel.code], scalars=False,
                    default_sort=[SchoolLevel.sort, SchoolLevel.grade_from])


def _check_level(db: Session, scope: OrgScope, code: str, grade_from: int, grade_to: int, level_id=None) -> str:
    code = (code or "").strip().lower()
    if not CODE_RE.match(code):
        raise validation("Mã cấp học: chữ thường không dấu, số, - _", "code")
    if grade_from > grade_to:
        raise validation("Khối bắt đầu phải nhỏ hơn hoặc bằng khối kết thúc", "grade_to")
    clash = db.scalar(select(SchoolLevel).where(SchoolLevel.organization_id == scope.org_id, SchoolLevel.code == code,
                                                SchoolLevel.id != level_id) if level_id else
                      select(SchoolLevel).where(SchoolLevel.organization_id == scope.org_id, SchoolLevel.code == code))
    if clash:
        raise conflict("Mã cấp học đã tồn tại", "code")
    overlap = db.scalar(select(SchoolLevel.name).where(
        SchoolLevel.organization_id == scope.org_id, SchoolLevel.grade_from <= grade_to, SchoolLevel.grade_to >= grade_from,
        *([SchoolLevel.id != level_id] if level_id else [])))
    if overlap:
        raise validation(f"Khoảng khối trùng với cấp {overlap}", "grade_from")
    return code


def create_level(db: Session, scope: OrgScope, code: str, name: str, grade_from: int, grade_to: int, sort: int = 0) -> SchoolLevel:
    _admin(scope)
    code = _check_level(db, scope, code, grade_from, grade_to)
    lv = SchoolLevel(organization_id=scope.org_id, code=code, name=name.strip(), grade_from=grade_from, grade_to=grade_to, sort=sort)
    db.add(lv)
    db.flush()
    audit.record(db, scope.user, scope.org_id, "level.create", "school_level", lv.id, code=code)
    return lv


def update_level(db: Session, scope: OrgScope, level_id, **changes) -> SchoolLevel:
    _admin(scope)
    lv = get_level(db, scope, level_id)
    code = changes.get("code") or lv.code
    lo = changes.get("grade_from") if changes.get("grade_from") is not None else lv.grade_from
    hi = changes.get("grade_to") if changes.get("grade_to") is not None else lv.grade_to
    code = _check_level(db, scope, code, lo, hi, lv.id)
    outside = db.scalar(select(func.count()).select_from(Grade).where(Grade.school_level_id == lv.id, (Grade.level < lo) | (Grade.level > hi)))
    if outside:
        raise validation(f"Còn {outside} khối nằm ngoài khoảng mới", "grade_from")
    lv.code, lv.grade_from, lv.grade_to = code, lo, hi
    if changes.get("name"):
        lv.name = changes["name"].strip()
    if changes.get("sort") is not None:
        lv.sort = changes["sort"]
    audit.record(db, scope.user, scope.org_id, "level.update", "school_level", lv.id)
    return lv


def delete_level(db: Session, scope: OrgScope, level_id) -> None:
    _admin(scope)
    lv = get_level(db, scope, level_id)
    n = db.scalar(select(func.count()).select_from(Grade).where(Grade.school_level_id == lv.id))
    if n:
        raise in_use(f"Cấp học còn {n} khối")
    db.delete(lv)
    audit.record(db, scope.user, scope.org_id, "level.delete", "school_level", lv.id, code=lv.code)


# ------------------------------------------------------------------ grades

CLASS_COUNT = select(func.count(SchoolClass.id)).where(SchoolClass.grade_id == Grade.id).correlate(Grade).scalar_subquery()
GRADE_COLS = {"level": Col(Grade.level, "number"), "name": Col(Grade.name), "school_level_id": Col(Grade.school_level_id, "uuid"),
              "class_count": Col(CLASS_COUNT, filterable=False)}


def get_grade(db: Session, scope: OrgScope, grade_id) -> Grade:
    g = db.get(Grade, grade_id)
    if g is None or g.organization_id != scope.org_id:
        raise not_found("Không tìm thấy khối")
    return g


def list_grades(db: Session, scope: OrgScope, params: ListParams):
    stmt = select(Grade, CLASS_COUNT).where(Grade.organization_id == scope.org_id)
    return paginate(db, stmt, params, GRADE_COLS, search=[Grade.name], scalars=False, default_sort=[Grade.level])


def _check_grade(db: Session, scope: OrgScope, level: int, school_level_id, grade_id=None) -> SchoolLevel:
    lv = get_level(db, scope, school_level_id)
    if not lv.grade_from <= level <= lv.grade_to:
        raise validation(f"{lv.name} gồm khối {lv.grade_from}–{lv.grade_to}", "level")
    clash = db.scalar(select(Grade.id).where(Grade.organization_id == scope.org_id, Grade.level == level,
                                             *([Grade.id != grade_id] if grade_id else [])))
    if clash:
        raise conflict(f"Khối {level} đã có", "level")
    return lv


def create_grade(db: Session, scope: OrgScope, level: int, school_level_id, name: str | None = None) -> Grade:
    _admin(scope)
    _check_grade(db, scope, level, school_level_id)
    g = Grade(organization_id=scope.org_id, level=level, name=(name or "").strip() or f"Lớp {level}", school_level_id=school_level_id)
    db.add(g)
    db.flush()
    audit.record(db, scope.user, scope.org_id, "grade.create", "grade", g.id, level=level)
    return g


def update_grade(db: Session, scope: OrgScope, grade_id, level=None, name=None, school_level_id=None) -> Grade:
    _admin(scope)
    g = get_grade(db, scope, grade_id)
    new_level = level if level is not None else g.level
    new_parent = school_level_id or g.school_level_id
    _check_grade(db, scope, new_level, new_parent, g.id)
    if new_level != g.level:
        # keep the classes' integer cache in step (A-03)
        for c in db.scalars(select(SchoolClass).where(SchoolClass.grade_id == g.id)):
            c.grade = new_level
    g.level, g.school_level_id = new_level, new_parent
    if name:
        g.name = name.strip()
    audit.record(db, scope.user, scope.org_id, "grade.update", "grade", g.id)
    return g


def delete_grade(db: Session, scope: OrgScope, grade_id) -> None:
    _admin(scope)
    g = get_grade(db, scope, grade_id)
    n = db.scalar(select(func.count()).select_from(SchoolClass).where(SchoolClass.grade_id == g.id))
    if n:
        raise in_use(f"Khối còn {n} lớp")
    db.delete(g)
    audit.record(db, scope.user, scope.org_id, "grade.delete", "grade", g.id, level=g.level)


def resolve_grade(db: Session, scope: OrgScope, grade_id=None, grade: int | None = None) -> Grade | None:
    """A class's grade from `grade_id`, or from a bare grade number (imports, old clients)."""
    if grade_id:
        return get_grade(db, scope, grade_id)
    if grade is not None:
        return db.scalar(select(Grade).where(Grade.organization_id == scope.org_id, Grade.level == grade))
    return None


# ------------------------------------------------------------------ tree

def tree(db: Session, scope: OrgScope, school_year: str | None = None, school_year_id=None) -> dict:
    members = (select(ClassMember.class_id, func.count().label("n")).group_by(ClassMember.class_id).subquery())
    cstmt = (select(SchoolClass, func.coalesce(members.c.n, 0)).outerjoin(members, members.c.class_id == SchoolClass.id)
             .where(SchoolClass.organization_id == scope.org_id).order_by(SchoolClass.name))
    if school_year:
        cstmt = cstmt.where(SchoolClass.school_year == school_year)
    if school_year_id:
        cstmt = cstmt.where(SchoolClass.school_year_id == school_year_id)
    by_grade: dict = {}
    for c, n in db.execute(cstmt):
        by_grade.setdefault(c.grade_id, []).append({"id": c.id, "name": c.name, "school_year": c.school_year, "member_count": n})
    grades_by_level: dict = {}
    for g in db.scalars(select(Grade).where(Grade.organization_id == scope.org_id).order_by(Grade.level)):
        cls = by_grade.get(g.id, [])
        grades_by_level.setdefault(g.school_level_id, []).append(
            {"id": g.id, "level": g.level, "name": g.name, "class_count": len(cls), "student_count": sum(c["member_count"] for c in cls), "classes": cls})
    levels = []
    for lv in db.scalars(select(SchoolLevel).where(SchoolLevel.organization_id == scope.org_id).order_by(SchoolLevel.sort, SchoolLevel.grade_from)):
        gs = grades_by_level.get(lv.id, [])
        levels.append({"id": lv.id, "code": lv.code, "name": lv.name, "grade_from": lv.grade_from, "grade_to": lv.grade_to,
                       "class_count": sum(g["class_count"] for g in gs), "student_count": sum(g["student_count"] for g in gs), "grades": gs})
    return {"levels": levels, "unassigned": by_grade.get(None, [])}
