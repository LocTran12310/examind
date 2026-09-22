"""Classes and membership (AC-19, AC-20)."""
import re

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.errors import conflict, not_found, validation
from app.deps import OrgScope
from app.models import ClassMember, SchoolClass, User
from app.services.paging import Col, ListParams, paginate
from app.services import audit

YEAR_RE = re.compile(r"^(\d{4})-(\d{4})$")


def current_school_year() -> str:
    from app.core.timezone import business_today

    d = business_today()
    start = d.year if d.month >= 8 else d.year - 1
    return f"{start}-{start + 1}"


def _check(name: str, school_year: str, grade: int | None):
    if not (name or "").strip():
        raise validation("Tên lớp không được để trống", "name")
    m = YEAR_RE.match(school_year or "")
    if not m or int(m.group(2)) != int(m.group(1)) + 1:
        raise validation("Năm học dạng 2026-2027", "school_year")
    if grade is not None and not 1 <= grade <= 12:
        raise validation("Khối lớp từ 1 đến 12", "grade")


def get_class(db: Session, scope: OrgScope, class_id) -> SchoolClass:
    c = db.get(SchoolClass, class_id)
    if c is None or c.organization_id != scope.org_id:
        raise not_found("Không tìm thấy lớp")
    return c


MEMBER_COUNT = func.count(ClassMember.user_id)
CLASS_COLS = {
    "name": Col(SchoolClass.name),
    "grade": Col(SchoolClass.grade, "number"),
    "grade_id": Col(SchoolClass.grade_id, "uuid"),
    "school_year": Col(SchoolClass.school_year, "exact"),
    "school_year_id": Col(SchoolClass.school_year_id, "uuid"),
    "member_count": Col(MEMBER_COUNT, filterable=False),
    "created_at": Col(SchoolClass.created_at, "date"),
}


def list_classes(db: Session, scope: OrgScope, params: ListParams):
    stmt = (select(SchoolClass, MEMBER_COUNT).outerjoin(ClassMember).where(SchoolClass.organization_id == scope.org_id)
            .group_by(SchoolClass.id))
    return paginate(db, stmt, params, CLASS_COLS, search=[SchoolClass.name], scalars=False,
                    default_sort=[SchoolClass.school_year.desc(), SchoolClass.name])


def find_or_create(db: Session, scope: OrgScope, name: str, school_year: str | None = None, grade: int | None = None) -> SchoolClass:
    school_year = school_year or _year(db, scope).code
    c = db.scalar(select(SchoolClass).where(SchoolClass.organization_id == scope.org_id, SchoolClass.name == name.strip(),
                                            SchoolClass.school_year == school_year))
    if c:
        return c
    if grade is None:
        m = re.match(r"^(\d{1,2})", name.strip())
        grade = int(m.group(1)) if m and 1 <= int(m.group(1)) <= 12 else None
    return create_class(db, scope, name, school_year, grade)


def _year(db: Session, scope: OrgScope, school_year: str | None = None, school_year_id=None):
    """The class's SchoolYear from an id, a code, or the org's active year (created when missing)."""
    from app.services import school_years

    if school_year_id:
        return school_years.get_year(db, scope, school_year_id)
    if school_year:
        _check("x", school_year, None)
        return school_years.ensure_year(db, scope.org_id, school_year, scope.user)
    active = school_years.active_year(db, scope.org_id)
    return active or school_years.ensure_year(db, scope.org_id, school_years.current_code(), scope.user)


def _audit_class(db: Session, scope: OrgScope, action: str, c: SchoolClass, **data) -> None:
    from app.models import SchoolYear

    y = db.get(SchoolYear, c.school_year_id) if c.school_year_id else None
    audit.record(db, scope.user, scope.org_id, action, "class", c.id, name=c.name, school_year=c.school_year,
                 closed_year=bool(y and y.status == "closed"), **data)


def create_class(db: Session, scope: OrgScope, name: str, school_year: str | None, grade: int | None, grade_id=None,
                 school_year_id=None) -> SchoolClass:
    from app.services.structure import resolve_grade

    y = _year(db, scope, school_year, school_year_id)
    school_year = y.code
    g = resolve_grade(db, scope, grade_id, grade)
    if g is not None:
        grade = g.level
    _check(name, school_year, grade)
    if db.scalar(select(SchoolClass.id).where(SchoolClass.organization_id == scope.org_id, SchoolClass.name == name.strip(),
                                              SchoolClass.school_year == school_year)):
        raise conflict("Lớp đã tồn tại trong năm học này", "name")
    c = SchoolClass(organization_id=scope.org_id, name=name.strip(), school_year=school_year, school_year_id=y.id, grade=grade,
                    grade_id=g.id if g else None)
    db.add(c)
    db.flush()
    _audit_class(db, scope, "class.create", c)
    return c


def update_class(db: Session, scope: OrgScope, class_id, name=None, school_year=None, grade=None, grade_id=None,
                 school_year_id=None) -> SchoolClass:
    from app.services.structure import resolve_grade

    c = get_class(db, scope, class_id)
    before = {"name": c.name, "school_year": c.school_year, "grade": c.grade}
    if school_year or school_year_id:
        y = _year(db, scope, school_year, school_year_id)
        school_year = y.code
        c.school_year_id = y.id
    g = resolve_grade(db, scope, grade_id, grade) if (grade_id or grade is not None) else None
    if g is not None:
        grade = g.level
    new_name = name.strip() if name is not None else c.name
    new_year = school_year or c.school_year
    _check(new_name, new_year, grade if grade is not None else c.grade)
    if (new_name, new_year) != (c.name, c.school_year) and db.scalar(
        select(SchoolClass.id).where(SchoolClass.organization_id == scope.org_id, SchoolClass.name == new_name,
                                     SchoolClass.school_year == new_year, SchoolClass.id != c.id)):
        raise conflict("Lớp đã tồn tại trong năm học này", "name")
    c.name, c.school_year = new_name, new_year
    if grade is not None:
        c.grade = grade
        c.grade_id = g.id if g else None
    after = {"name": c.name, "school_year": c.school_year, "grade": c.grade}
    _audit_class(db, scope, "class.update", c, changes={k: [before[k], after[k]] for k in after if before[k] != after[k]})
    return c


def delete_class(db: Session, scope: OrgScope, class_id) -> None:
    c = get_class(db, scope, class_id)
    _audit_class(db, scope, "class.delete", c)
    db.delete(c)


def members(db: Session, scope: OrgScope, class_id) -> list[User]:
    get_class(db, scope, class_id)
    return db.scalars(select(User).join(ClassMember, ClassMember.user_id == User.id)
                      .where(ClassMember.class_id == class_id).order_by(User.full_name)).all()


def add_members(db: Session, scope: OrgScope, class_id, user_ids) -> int:
    get_class(db, scope, class_id)
    ids = set(user_ids)
    from app.services.membership import member_ids

    valid = member_ids(db, scope.org_id, ids)
    if ids - valid:
        raise not_found("Không tìm thấy người dùng")
    if valid:
        db.execute(insert(ClassMember).values([{"class_id": class_id, "user_id": u} for u in valid]).on_conflict_do_nothing())
        _audit_class(db, scope, "class.members_add", get_class(db, scope, class_id), user_ids=[str(u) for u in valid])
    return len(valid)


def remove_member(db: Session, scope: OrgScope, class_id, user_id) -> None:
    c = get_class(db, scope, class_id)
    db.execute(delete(ClassMember).where(ClassMember.class_id == class_id, ClassMember.user_id == user_id))
    _audit_class(db, scope, "class.members_remove", c, user_ids=[str(user_id)])
