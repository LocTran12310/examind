from datetime import date, datetime
import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.modules.academic.domain.entities import Grade, SchoolClass, SchoolLevel, SchoolYear
from app.modules.academic.infrastructure import orm  # noqa: F401  (mapping)
from app.shared.infrastructure.schema.academic import class_members, classes, school_years
from app.shared.infrastructure.schema.identity import organization_members, users
from app.shared.infrastructure.schema.taxonomy import grades, school_levels


class _Repo:
    def __init__(self, session: Session):
        self.session = session

    def _owned(self, cls, org_id: uuid.UUID, id_: uuid.UUID):
        row = self.session.get(cls, id_)
        return row if row is not None and row.organization_id == org_id else None

    def add(self, row) -> None:
        self.session.add(row)
        self.session.flush()

    def remove(self, row) -> None:
        self.session.delete(row)
        self.session.flush()

    def flush(self) -> None:
        self.session.flush()


class SqlSchoolYearRepository(_Repo):
    def get(self, org_id: uuid.UUID, year_id: uuid.UUID) -> SchoolYear | None:
        return self._owned(SchoolYear, org_id, year_id)

    def by_code(self, org_id: uuid.UUID, code: str) -> SchoolYear | None:
        return self.session.scalar(select(SchoolYear).where(school_years.c.organization_id == org_id, school_years.c.code == code))

    def active(self, org_id: uuid.UUID) -> SchoolYear | None:
        return self.session.scalar(select(SchoolYear).where(school_years.c.organization_id == org_id, school_years.c.status == "active"))

    def covering(self, org_id: uuid.UUID, day: date) -> SchoolYear | None:
        y = school_years.c
        return self.session.scalar(select(SchoolYear).where(y.organization_id == org_id, y.start_date <= day, y.end_date >= day)
                                   .order_by(y.start_date.desc()).limit(1))

    def class_count(self, year_id: uuid.UUID) -> int:
        return self.session.scalar(select(func.count()).select_from(classes).where(classes.c.school_year_id == year_id)) or 0


class SqlClassRepository(_Repo):
    def get(self, org_id: uuid.UUID, class_id: uuid.UUID) -> SchoolClass | None:
        return self._owned(SchoolClass, org_id, class_id)

    def find(self, org_id: uuid.UUID, name: str, school_year: str, exclude_id: uuid.UUID | None = None) -> SchoolClass | None:
        stmt = select(SchoolClass).where(classes.c.organization_id == org_id, classes.c.name == name, classes.c.school_year == school_year)
        if exclude_id is not None:
            stmt = stmt.where(classes.c.id != exclude_id)
        return self.session.scalar(stmt.limit(1))

    def in_year(self, year_id: uuid.UUID, name: str) -> SchoolClass | None:
        return self.session.scalar(select(SchoolClass).where(classes.c.school_year_id == year_id, classes.c.name == name))

    def names_in_year(self, year_id: uuid.UUID) -> set[str]:
        return set(self.session.scalars(select(classes.c.name).where(classes.c.school_year_id == year_id)))

    def of_year(self, year_id: uuid.UUID) -> list[SchoolClass]:
        return list(self.session.scalars(select(SchoolClass).where(classes.c.school_year_id == year_id).order_by(classes.c.grade, classes.c.name)))

    def with_grade(self, grade_id: uuid.UUID) -> list[SchoolClass]:
        return list(self.session.scalars(select(SchoolClass).where(classes.c.grade_id == grade_id)))

    def add_members(self, class_id: uuid.UUID, user_ids: set[uuid.UUID]) -> None:
        self.session.execute(insert(class_members).values([{"class_id": class_id, "user_id": u} for u in user_ids]).on_conflict_do_nothing())

    def enroll(self, class_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.session.execute(insert(class_members).values(class_id=class_id, user_id=user_id, status="active")
                             .on_conflict_do_update(index_elements=["class_id", "user_id"], set_={"status": "active", "left_at": None}))

    def leave(self, class_id: uuid.UUID, user_id: uuid.UUID, status: str, at: datetime) -> None:
        self.session.execute(update(class_members).where(class_members.c.class_id == class_id, class_members.c.user_id == user_id)
                             .values(status=status, left_at=at))

    def remove_member(self, class_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.session.execute(delete(class_members).where(class_members.c.class_id == class_id, class_members.c.user_id == user_id))

    def member_ids(self, class_id: uuid.UUID) -> list[uuid.UUID]:
        return list(self.session.scalars(select(users.c.id).join(class_members, class_members.c.user_id == users.c.id)
                                         .where(class_members.c.class_id == class_id).order_by(users.c.full_name)))


class SqlLevelRepository(_Repo):
    def get(self, org_id: uuid.UUID, level_id: uuid.UUID) -> SchoolLevel | None:
        return self._owned(SchoolLevel, org_id, level_id)

    def code_taken(self, org_id: uuid.UUID, code: str, exclude_id: uuid.UUID | None = None) -> bool:
        lv = school_levels.c
        stmt = select(lv.id).where(lv.organization_id == org_id, lv.code == code)
        if exclude_id is not None:
            stmt = stmt.where(lv.id != exclude_id)
        return self.session.scalar(stmt.limit(1)) is not None

    def overlapping(self, org_id: uuid.UUID, grade_from: int, grade_to: int, exclude_id: uuid.UUID | None = None) -> str | None:
        lv = school_levels.c
        stmt = select(lv.name).where(lv.organization_id == org_id, lv.grade_from <= grade_to, lv.grade_to >= grade_from)
        if exclude_id is not None:
            stmt = stmt.where(lv.id != exclude_id)
        return self.session.scalar(stmt.limit(1))

    def grade_count(self, level_id: uuid.UUID) -> int:
        return self.session.scalar(select(func.count()).select_from(grades).where(grades.c.school_level_id == level_id)) or 0

    def grades_outside(self, level_id: uuid.UUID, grade_from: int, grade_to: int) -> int:
        g = grades.c
        return self.session.scalar(select(func.count()).select_from(grades).where(
            g.school_level_id == level_id, (g.level < grade_from) | (g.level > grade_to))) or 0


class SqlGradeRepository(_Repo):
    def get(self, org_id: uuid.UUID, grade_id: uuid.UUID) -> Grade | None:
        return self._owned(Grade, org_id, grade_id)

    def by_level(self, org_id: uuid.UUID, level: int) -> Grade | None:
        return self.session.scalar(select(Grade).where(grades.c.organization_id == org_id, grades.c.level == level))

    def level_taken(self, org_id: uuid.UUID, level: int, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = select(grades.c.id).where(grades.c.organization_id == org_id, grades.c.level == level)
        if exclude_id is not None:
            stmt = stmt.where(grades.c.id != exclude_id)
        return self.session.scalar(stmt.limit(1)) is not None

    def top_level(self, org_id: uuid.UUID) -> int | None:
        return self.session.scalar(select(func.max(grades.c.level)).where(grades.c.organization_id == org_id))

    def class_count(self, grade_id: uuid.UUID) -> int:
        return self.session.scalar(select(func.count()).select_from(classes).where(classes.c.grade_id == grade_id)) or 0


class SqlMemberDirectory:
    """MemberDirectory over the memberships (a user belongs to an org through an active organization_members row)."""

    def __init__(self, session: Session):
        self.session = session

    def member_ids(self, org_id: uuid.UUID, user_ids: set[uuid.UUID]) -> set[uuid.UUID]:
        if not user_ids:
            return set()
        m = organization_members.c
        return set(self.session.scalars(select(m.user_id).where(m.organization_id == org_id, m.is_active.is_(True), m.user_id.in_(list(user_ids)))))

    def roles(self, org_id: uuid.UUID, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        if not user_ids:
            return {}
        m = organization_members.c
        return dict(self.session.execute(select(m.user_id, m.role).where(
            m.organization_id == org_id, m.user_id.in_(list(user_ids)), m.is_active.is_(True))).all())
