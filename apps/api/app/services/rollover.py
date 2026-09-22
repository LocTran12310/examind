"""Chuyển năm học: preview → commit, idempotent by (target year, class name) (school-years ADR-03, A-07)."""
import re

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.errors import forbidden, validation
from app.core.security import now
from app.deps import OrgScope
from app.models import ClassMember, Grade, SchoolClass, User
from app.services import audit, school_years
from app.services.membership import roles_in

ACTIONS = {"promote": "promoted", "retain": "retained", "transfer": "transferred", "graduate": "graduated"}
LEADING = re.compile(r"^(\d{1,2})(.*)$")


def next_code(code: str) -> str:
    a = int(code[5:])
    return f"{a}-{a + 1}"


def next_name(name: str, grade: int | None) -> tuple[str, int | None]:
    """10A1 → (11A1, 11); a name without a leading number keeps its name and moves up a grade."""
    m = LEADING.match(name.strip())
    if m:
        n = int(m.group(1)) + 1
        return f"{n}{m.group(2)}", n
    return name.strip(), (grade + 1) if grade else None


def _grade_row(db: Session, org_id, level: int | None):
    return db.scalar(select(Grade).where(Grade.organization_id == org_id, Grade.level == level)) if level else None


def preview(db: Session, scope: OrgScope, source_year_id, target_code: str | None = None) -> dict:
    if scope.role != "org_admin":
        raise forbidden()
    src = school_years.get_year(db, scope, source_year_id)
    target_code = target_code or next_code(src.code)
    if target_code <= src.code:
        raise validation("Năm học mới phải sau năm hiện tại", "target_code")
    top = db.scalar(select(func.max(Grade.level)).where(Grade.organization_id == scope.org_id)) or 12
    target = db.scalar(select(school_years.SchoolYear).where(school_years.SchoolYear.organization_id == scope.org_id,
                                                              school_years.SchoolYear.code == target_code))
    existing = set(db.scalars(select(SchoolClass.name).where(SchoolClass.school_year_id == target.id))) if target else set()
    classes = []
    for c in db.scalars(select(SchoolClass).where(SchoolClass.school_year_id == src.id).order_by(SchoolClass.grade, SchoolClass.name)):
        rows = db.execute(select(User, ClassMember.status).join(ClassMember, ClassMember.user_id == User.id)
                          .where(ClassMember.class_id == c.id).order_by(User.full_name)).all()
        roles = roles_in(db, scope.org_id, [u.id for u, _ in rows])
        grade = c.grade
        graduating = grade is not None and grade >= top
        tname, tgrade = (None, None) if graduating else next_name(c.name, grade)
        classes.append({
            "source_class_id": c.id, "source_name": c.name, "grade": grade, "graduating": graduating,
            "target_name": tname, "target_grade": tgrade, "target_exists": bool(tname and tname in existing),
            "students": [{"user_id": u.id, "full_name": u.full_name, "username": u.username, "current_status": st,
                          "action": "graduate" if graduating else "promote"}
                         for u, st in rows if roles.get(u.id) == "student"],
        })
    return {"source_year": {"id": src.id, "code": src.code, "status": src.status}, "target_code": target_code,
            "target_year_id": target.id if target else None, "top_grade": top, "classes": classes}


def _target_class(db: Session, scope: OrgScope, year, name: str, level: int | None, cache: dict, created: list) -> SchoolClass:
    key = (year.id, name)
    if key in cache:
        return cache[key]
    c = db.scalar(select(SchoolClass).where(SchoolClass.school_year_id == year.id, SchoolClass.name == name))
    if c is None:
        g = _grade_row(db, scope.org_id, level)
        c = SchoolClass(organization_id=scope.org_id, name=name, school_year=year.code, school_year_id=year.id,
                        grade=level, grade_id=g.id if g else None)
        db.add(c)
        db.flush()
        created.append(c.name)
    cache[key] = c
    return c


def commit(db: Session, scope: OrgScope, source_year_id, target_code: str, classes: list[dict], activate_target: bool = False) -> dict:
    if scope.role != "org_admin":
        raise forbidden()
    src = school_years.get_year(db, scope, source_year_id)
    if target_code <= src.code:
        raise validation("Năm học mới phải sau năm hiện tại", "target_code")
    target = school_years.ensure_year(db, scope.org_id, target_code, scope.user)
    counts = {a: 0 for a in ACTIONS}
    created: list[str] = []
    cache: dict = {}
    stamp = now()
    for item in classes:
        c = db.get(SchoolClass, item["source_class_id"])
        if c is None or c.school_year_id != src.id:
            raise validation("Lớp không thuộc năm học nguồn", "classes")
        for s in item.get("students", []):
            action = s.get("action")
            if action not in ACTIONS:
                raise validation("Thao tác không hợp lệ", "classes")
            dest = None
            if action == "promote":
                name = (item.get("target_name") or "").strip() or next_name(c.name, c.grade)[0]
                dest = _target_class(db, scope, target, name, next_name(c.name, c.grade)[1], cache, created)
            elif action == "retain":
                dest = _target_class(db, scope, target, c.name, c.grade, cache, created)
            if dest is not None:
                db.execute(insert(ClassMember).values(class_id=dest.id, user_id=s["user_id"], status="active")
                           .on_conflict_do_update(index_elements=["class_id", "user_id"], set_={"status": "active", "left_at": None}))
            db.execute(ClassMember.__table__.update().where(ClassMember.class_id == c.id, ClassMember.user_id == s["user_id"])
                       .values(status=ACTIONS[action], left_at=stamp))
            counts[action] += 1
    if activate_target:
        school_years.set_status(db, scope, target.id, "active")
    audit.record(db, scope.user, scope.org_id, "rollover.commit", "school_year", src.id, code=src.code, target=target.code,
                 classes_created=created, **counts, closed_year=src.status == "closed")
    return {"target_year_id": target.id, "target_code": target.code, "classes_created": created, **counts}
