"""Classes and membership (AC-19, AC-20)."""
import re

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.errors import conflict, not_found, validation
from app.deps import OrgScope
from app.models import ClassMember, SchoolClass, User
from app.services import audit

YEAR_RE = re.compile(r"^(\d{4})-(\d{4})$")


def current_school_year() -> str:
    from datetime import date

    d = date.today()
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


def list_classes(db: Session, scope: OrgScope, school_year: str | None = None):
    stmt = select(SchoolClass, func.count(ClassMember.user_id)).outerjoin(ClassMember).where(SchoolClass.organization_id == scope.org_id)
    if school_year:
        stmt = stmt.where(SchoolClass.school_year == school_year)
    return db.execute(stmt.group_by(SchoolClass.id).order_by(SchoolClass.school_year.desc(), SchoolClass.name)).all()


def find_or_create(db: Session, scope: OrgScope, name: str, school_year: str | None = None, grade: int | None = None) -> SchoolClass:
    school_year = school_year or current_school_year()
    c = db.scalar(select(SchoolClass).where(SchoolClass.organization_id == scope.org_id, SchoolClass.name == name.strip(),
                                            SchoolClass.school_year == school_year))
    if c:
        return c
    if grade is None:
        m = re.match(r"^(\d{1,2})", name.strip())
        grade = int(m.group(1)) if m and 1 <= int(m.group(1)) <= 12 else None
    return create_class(db, scope, name, school_year, grade)


def create_class(db: Session, scope: OrgScope, name: str, school_year: str, grade: int | None) -> SchoolClass:
    _check(name, school_year, grade)
    if db.scalar(select(SchoolClass.id).where(SchoolClass.organization_id == scope.org_id, SchoolClass.name == name.strip(),
                                              SchoolClass.school_year == school_year)):
        raise conflict("Lớp đã tồn tại trong năm học này", "name")
    c = SchoolClass(organization_id=scope.org_id, name=name.strip(), school_year=school_year, grade=grade)
    db.add(c)
    db.flush()
    audit.record(db, scope.user, scope.org_id, "class.create", "class", c.id, name=c.name)
    return c


def update_class(db: Session, scope: OrgScope, class_id, name=None, school_year=None, grade=None) -> SchoolClass:
    c = get_class(db, scope, class_id)
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
    return c


def delete_class(db: Session, scope: OrgScope, class_id) -> None:
    c = get_class(db, scope, class_id)
    db.delete(c)
    audit.record(db, scope.user, scope.org_id, "class.delete", "class", c.id, name=c.name)


def members(db: Session, scope: OrgScope, class_id) -> list[User]:
    get_class(db, scope, class_id)
    return db.scalars(select(User).join(ClassMember, ClassMember.user_id == User.id)
                      .where(ClassMember.class_id == class_id).order_by(User.full_name)).all()


def add_members(db: Session, scope: OrgScope, class_id, user_ids) -> int:
    get_class(db, scope, class_id)
    ids = set(user_ids)
    valid = set(db.scalars(select(User.id).where(User.id.in_(ids), User.organization_id == scope.org_id)))
    if ids - valid:
        raise not_found("Không tìm thấy người dùng")
    if valid:
        db.execute(insert(ClassMember).values([{"class_id": class_id, "user_id": u} for u in valid]).on_conflict_do_nothing())
    return len(valid)


def remove_member(db: Session, scope: OrgScope, class_id, user_id) -> None:
    get_class(db, scope, class_id)
    db.execute(delete(ClassMember).where(ClassMember.class_id == class_id, ClassMember.user_id == user_id))
