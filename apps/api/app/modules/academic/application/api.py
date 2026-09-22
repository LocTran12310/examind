"""What other contexts may ask the academic context (architecture-refactor ADR-01)."""
from datetime import date, datetime
import uuid

from app.modules.academic.application.commands.create_class import CreateClass, create_class
from app.modules.academic.application.common import ensure_year, load_class
from app.modules.academic.domain.entities import SchoolClass, SchoolYear
from app.modules.academic.domain.ports import ClassRepository, GradeRepository, SchoolYearRepository
from app.modules.academic.domain.services import calendar
from app.modules.academic.domain.services.structure import grade_from_name
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.application.calendar import BusinessCalendar


class AcademicApi:
    def __init__(self, years: SchoolYearRepository, classes: ClassRepository, grades: GradeRepository, audit: AuditTrail,
                 cal: BusinessCalendar):
        self.years, self.classes, self.grades, self.audit, self.cal = years, classes, grades, audit, cal

    def current_code(self, today: date | None = None) -> str:
        return calendar.current_code(today or self.cal.today())

    def active_year(self, org_id: uuid.UUID) -> SchoolYear | None:
        return self.years.active(org_id)

    def year_for_date(self, org_id: uuid.UUID, when: date | datetime) -> SchoolYear | None:
        return self.years.covering(org_id, self.cal.day_of(when))

    def term_for_date(self, year: SchoolYear | None, when: date | datetime) -> str | None:
        return calendar.term_for_date(year, self.cal.day_of(when))

    def ensure_year(self, org_id: uuid.UUID, code: str, actor: Actor | None = None) -> SchoolYear:
        """Flushed, not committed: the caller's transaction owns it."""
        return ensure_year(self.years, self.audit, self.cal, org_id, code, actor)

    def find_or_create_class(self, actor: Actor, name: str, school_year: str | None = None, grade: int | None = None) -> SchoolClass:
        """A class of the active year by name (imports); the grade is read from the name ("10A1" → 10) when not given."""
        school_year = school_year or (self.years.active(actor.org_id) or self.ensure_year(actor.org_id, self.current_code(), actor)).code
        c = self.classes.find(actor.org_id, name.strip(), school_year)
        if c is not None:
            return c
        return create_class(self.years, self.classes, self.grades, self.audit, self.cal, actor,
                            CreateClass(name, school_year, grade if grade is not None else grade_from_name(name)))

    def member_ids(self, actor: Actor, class_id: uuid.UUID) -> list[uuid.UUID]:
        """Members of a class of the org, by full name."""
        return self.classes.member_ids(load_class(self.classes, actor.org_id, class_id).id)

    def add_members(self, actor: Actor, class_id: uuid.UUID, user_ids: set[uuid.UUID]) -> None:
        """Enrol accounts the caller already checked (user import); flushed with the caller's transaction."""
        self.classes.add_members(load_class(self.classes, actor.org_id, class_id).id, set(user_ids))

    def leave_org_classes(self, org_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """The account leaves every class of the org (its membership there ended)."""
        self.classes.remove_from_org(org_id, user_id)

    # ------------------------------------------------------------------ assessment (assignments, answer-fact snapshots)

    def class_names(self, org_id: uuid.UUID, class_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """{class_id: name} for the classes of the org among `class_ids` (unknown or foreign ids are left out)."""
        return self.classes.names(org_id, list(class_ids))

    def members_of(self, org_id: uuid.UUID, class_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        """Every account enrolled in one of these classes of the org (whatever the enrollment status)."""
        return self.classes.members_of(org_id, list(class_ids))

    def classes_of(self, org_id: uuid.UUID, user_id: uuid.UUID, year_id: uuid.UUID | None = None) -> list[uuid.UUID]:
        """The classes of the org the account is enrolled in (of that school year when given)."""
        return self.classes.classes_of(org_id, user_id, year_id)
