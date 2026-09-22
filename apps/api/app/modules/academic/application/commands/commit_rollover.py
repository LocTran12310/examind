"""Chuyển năm học: apply the (edited) plan, idempotent by (target year, class name) (school-years ADR-03, A-07)."""
from dataclasses import dataclass, field
import uuid

from app.modules.academic.application.common import ensure_year, load_year, require_admin, set_status
from app.modules.academic.domain.entities import SchoolClass, SchoolYear
from app.modules.academic.domain.ports import ClassRepository, GradeRepository, SchoolYearRepository
from app.modules.academic.domain.services.rollover import ACTIONS, next_name
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.calendar import BusinessCalendar
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.clock import utcnow
from app.shared.domain.errors import Invalid


@dataclass(frozen=True)
class RolloverStudent:
    user_id: uuid.UUID
    action: str  # promote | retain | transfer | graduate


@dataclass(frozen=True)
class RolloverClass:
    source_class_id: uuid.UUID
    target_name: str | None = None
    students: list[RolloverStudent] = field(default_factory=list)


@dataclass(frozen=True)
class CommitRollover:
    source_year_id: uuid.UUID
    target_code: str
    classes: list[RolloverClass]
    activate_target: bool = False


class CommitRolloverHandler:
    """promote → the next class (created when missing), retain → the same name in the new year, transfer/graduate →
    no class; the source membership keeps the outcome as its status. Running it again creates nothing new."""

    def __init__(self, years: SchoolYearRepository, classes: ClassRepository, grades: GradeRepository, audit: AuditTrail,
                 cal: BusinessCalendar, uow: UnitOfWork):
        self.years, self.classes, self.grades, self.audit, self.cal, self.uow = years, classes, grades, audit, cal, uow

    def __call__(self, actor: Actor, cmd: CommitRollover) -> dict:
        require_admin(actor)
        src = load_year(self.years, actor.org_id, cmd.source_year_id)
        if cmd.target_code <= src.code:
            raise Invalid("Năm học mới phải sau năm hiện tại", "target_code")
        target = ensure_year(self.years, self.audit, self.cal, actor.org_id, cmd.target_code, actor)
        counts = {a: 0 for a in ACTIONS}
        created: list[str] = []
        cache: dict = {}
        stamp = utcnow()
        for item in cmd.classes:
            c = self.classes.get(actor.org_id, item.source_class_id)
            if c is None or c.school_year_id != src.id:
                raise Invalid("Lớp không thuộc năm học nguồn", "classes")
            for s in item.students:
                if s.action not in ACTIONS:
                    raise Invalid("Thao tác không hợp lệ", "classes")
                dest = None
                if s.action == "promote":
                    up_name, up_grade = next_name(c.name, c.grade)
                    dest = self._target_class(actor, target, (item.target_name or "").strip() or up_name, up_grade, cache, created)
                elif s.action == "retain":
                    dest = self._target_class(actor, target, c.name, c.grade, cache, created)
                if dest is not None:
                    self.classes.enroll(dest.id, s.user_id)
                self.classes.leave(c.id, s.user_id, ACTIONS[s.action], stamp)
                counts[s.action] += 1
        if cmd.activate_target:
            set_status(self.years, self.audit, actor, target, "active")
        self.audit.record(actor, actor.org_id, "rollover.commit", "school_year", src.id, code=src.code, target=target.code,
                          classes_created=created, **counts, closed_year=src.status == "closed")
        self.uow.commit()
        return {"target_year_id": target.id, "target_code": target.code, "classes_created": created, **counts}

    def _target_class(self, actor: Actor, year: SchoolYear, name: str, level: int | None, cache: dict, created: list) -> SchoolClass:
        key = (year.id, name)
        if key in cache:
            return cache[key]
        c = self.classes.in_year(year.id, name)
        if c is None:
            g = self.grades.by_level(actor.org_id, level) if level else None
            c = SchoolClass(organization_id=actor.org_id, name=name, school_year=year.code, school_year_id=year.id,
                            grade=level, grade_id=g.id if g else None)
            self.classes.add(c)
            created.append(c.name)
        cache[key] = c
        return c
