"""Academic handlers against in-memory ports: school years, classes, members, rollover, structure (ADR-02)."""
from datetime import date
import uuid

import pytest

from app.modules.academic.application.commands.add_members import AddMembers, AddMembersHandler
from app.modules.academic.application.commands.change_year_status import ChangeYearStatus, ChangeYearStatusHandler
from app.modules.academic.application.commands.commit_rollover import CommitRollover, CommitRolloverHandler, RolloverClass, RolloverStudent
from app.modules.academic.application.commands.create_class import CreateClass, CreateClassHandler
from app.modules.academic.application.commands.create_grade import CreateGrade, CreateGradeHandler
from app.modules.academic.application.commands.create_level import CreateLevel, CreateLevelHandler
from app.modules.academic.application.commands.create_year import CreateYear, CreateYearHandler
from app.modules.academic.application.commands.delete_level import DeleteLevel, DeleteLevelHandler
from app.modules.academic.application.commands.delete_year import DeleteYear, DeleteYearHandler
from app.modules.academic.application.commands.update_grade import UpdateGrade, UpdateGradeHandler
from app.modules.academic.domain.services.calendar import current_code, term_for_date
from app.modules.academic.domain.services.rollover import next_name
from app.shared.application.actor import Actor
from app.shared.domain.errors import Conflict, Forbidden, Invalid, NotFound
from tests.unit.fakes import FakeAudit, FakeUow

ORG = uuid.uuid4()
ADMIN = Actor(user_id=uuid.uuid4(), org_id=ORG, role="org_admin")
TEACHER = Actor(user_id=uuid.uuid4(), org_id=ORG, role="teacher")
TODAY = date(2026, 10, 1)


class Rows:
    def __init__(self):
        self.rows = {}

    def get(self, org_id, id_):
        r = self.rows.get(id_)
        return r if r is not None and r.organization_id == org_id else None

    def add(self, r):
        self.rows[r.id] = r

    def remove(self, r):
        del self.rows[r.id]

    def flush(self):
        pass


class FakeYears(Rows):
    def __init__(self, classes):
        super().__init__()
        self.classes = classes

    def by_code(self, org_id, code):
        return next((y for y in self.rows.values() if y.organization_id == org_id and y.code == code), None)

    def active(self, org_id):
        return next((y for y in self.rows.values() if y.organization_id == org_id and y.status == "active"), None)

    def covering(self, org_id, day):
        return next((y for y in self.rows.values() if y.start_date <= day <= y.end_date), None)

    def class_count(self, year_id):
        return sum(1 for c in self.classes.rows.values() if c.school_year_id == year_id)


class FakeClasses(Rows):
    def __init__(self):
        super().__init__()
        self.members = {}  # (class_id, user_id) -> status

    def find(self, org_id, name, school_year, exclude_id=None):
        return next((c for c in self.rows.values() if (c.organization_id, c.name, c.school_year) == (org_id, name, school_year) and c.id != exclude_id), None)

    def in_year(self, year_id, name):
        return next((c for c in self.rows.values() if c.school_year_id == year_id and c.name == name), None)

    def names_in_year(self, year_id):
        return {c.name for c in self.rows.values() if c.school_year_id == year_id}

    def of_year(self, year_id):
        return sorted((c for c in self.rows.values() if c.school_year_id == year_id), key=lambda c: (c.grade or 0, c.name))

    def with_grade(self, grade_id):
        return [c for c in self.rows.values() if c.grade_id == grade_id]

    def add_members(self, class_id, user_ids):
        for u in user_ids:
            self.members.setdefault((class_id, u), "active")

    def enroll(self, class_id, user_id):
        self.members[(class_id, user_id)] = "active"

    def leave(self, class_id, user_id, status, at):
        if (class_id, user_id) in self.members:
            self.members[(class_id, user_id)] = status

    def remove_member(self, class_id, user_id):
        self.members.pop((class_id, user_id), None)

    def member_ids(self, class_id):
        return [u for c, u in self.members if c == class_id]

    def of(self, class_id):
        return {u for c, u in self.members if c == class_id}


class FakeGrades(Rows):
    def __init__(self, classes):
        super().__init__()
        self.classes = classes

    def by_level(self, org_id, level):
        return next((g for g in self.rows.values() if g.organization_id == org_id and g.level == level), None)

    def level_taken(self, org_id, level, exclude_id=None):
        return any(g.organization_id == org_id and g.level == level and g.id != exclude_id for g in self.rows.values())

    def top_level(self, org_id):
        return max((g.level for g in self.rows.values()), default=None)

    def class_count(self, grade_id):
        return len(self.classes.with_grade(grade_id))


class FakeLevels(Rows):
    def __init__(self, grades):
        super().__init__()
        self.grades = grades

    def code_taken(self, org_id, code, exclude_id=None):
        return any(lv.code == code and lv.id != exclude_id for lv in self.rows.values())

    def overlapping(self, org_id, lo, hi, exclude_id=None):
        return next((lv.name for lv in self.rows.values() if lv.grade_from <= hi and lv.grade_to >= lo and lv.id != exclude_id), None)

    def grade_count(self, level_id):
        return sum(1 for g in self.grades.rows.values() if g.school_level_id == level_id)

    def grades_outside(self, level_id, lo, hi):
        return sum(1 for g in self.grades.rows.values() if g.school_level_id == level_id and not lo <= g.level <= hi)


class FakeDirectory:
    def __init__(self, *ids):
        self.ids = set(ids)

    def member_ids(self, org_id, user_ids):
        return set(user_ids) & self.ids if org_id == ORG else set()

    def roles(self, org_id, user_ids):
        return {u: "student" for u in user_ids}


class FakeCalendar:
    def today(self):
        return TODAY

    def day_of(self, when):
        return when


@pytest.fixture
def ports():
    classes = FakeClasses()
    years = FakeYears(classes)
    grades = FakeGrades(classes)
    return years, classes, grades, FakeLevels(grades), FakeAudit(), FakeCalendar(), FakeUow()


def test_calendar_rules():
    assert current_code(date(2026, 8, 1)) == "2026-2027" and current_code(date(2027, 5, 1)) == "2026-2027"
    assert next_name("10A1", 10) == ("11A1", 11) and next_name("Lớp hè", 10) == ("Lớp hè", 11)


def test_years_create_activate_and_delete_guards(ports):
    years, classes, grades, _, audit, cal, uow = ports
    create = CreateYearHandler(years, audit, uow)
    with pytest.raises(Forbidden):
        create(TEACHER, CreateYear("2026-2027"))
    with pytest.raises(Invalid):
        create(ADMIN, CreateYear("2026-2028"))
    y1 = create(ADMIN, CreateYear("2026-2027"))
    assert (y1.status, y1.start_date, [t.code for t in y1.terms]) == ("planning", date(2026, 9, 5), ["hk1", "hk2"])
    assert term_for_date(years.rows[y1.id], date(2027, 3, 1)) == "hk2"
    with pytest.raises(Conflict):
        create(ADMIN, CreateYear("2026-2027"))
    with pytest.raises(Invalid):  # a term outside the year
        create(ADMIN, CreateYear("2027-2028", terms=[{"code": "hk1", "start_date": date(2027, 8, 1), "end_date": date(2028, 1, 15)}]))
    y2 = create(ADMIN, CreateYear("2027-2028"))
    status = ChangeYearStatusHandler(years, audit, uow)
    status(ADMIN, ChangeYearStatus(y1.id, "active"))
    status(ADMIN, ChangeYearStatus(y2.id, "active"))
    assert (years.rows[y1.id].status, years.rows[y2.id].status) == ("closed", "active")  # only one active year
    delete = DeleteYearHandler(years, audit, uow)
    with pytest.raises(Conflict):
        delete(ADMIN, DeleteYear(y2.id))  # the active year
    CreateClassHandler(years, classes, grades, audit, cal, uow)(ADMIN, CreateClass("10A1", school_year_id=y1.id))
    with pytest.raises(Conflict) as e:
        delete(ADMIN, DeleteYear(y1.id))
    assert e.value.code == "in_use" and e.value.message == "Năm học còn 1 lớp"


def test_class_goes_to_the_active_year_created_on_demand_and_members_stay_in_the_org(ports):
    years, classes, grades, _, audit, cal, uow = ports
    create = CreateClassHandler(years, classes, grades, audit, cal, uow)
    c = create(TEACHER, CreateClass("  10A1 "))
    y = years.by_code(ORG, "2026-2027")
    assert (c.name, c.school_year, c.school_year_id, y.status) == ("10A1", "2026-2027", y.id, "active")  # current year, no active one yet
    assert audit.actions()[:2] == ["year.create", "class.create"]
    with pytest.raises(Conflict):
        create(TEACHER, CreateClass("10A1"))
    with pytest.raises(Invalid):
        create(TEACHER, CreateClass("10A2", school_year="2026-2028"))
    old = create(TEACHER, CreateClass("12C", school_year="2029-2030"))
    assert years.by_code(ORG, "2029-2030").status == "planning" and old.school_year == "2029-2030"
    a, b, stranger = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    add = AddMembersHandler(years, classes, FakeDirectory(a, b), audit, uow)
    assert add(TEACHER, AddMembers(c.id, [a, b, a])) == 2
    add(TEACHER, AddMembers(c.id, [a]))  # idempotent
    assert classes.of(c.id) == {a, b}
    with pytest.raises(NotFound):
        add(TEACHER, AddMembers(c.id, [stranger]))


def test_rollover_promotes_retains_and_is_idempotent(ports):
    years, classes, grades, _, audit, cal, uow = ports
    y = CreateYearHandler(years, audit, uow)(ADMIN, CreateYear("2026-2027"))
    ChangeYearStatusHandler(years, audit, uow)(ADMIN, ChangeYearStatus(y.id, "active"))
    k10 = CreateClassHandler(years, classes, grades, audit, cal, uow)(ADMIN, CreateClass("10A1", grade=10))
    an, binh, chi = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    classes.add_members(k10.id, {an, binh, chi})
    commit = CommitRolloverHandler(years, classes, grades, audit, cal, uow)
    plan = [RolloverClass(k10.id, None, [RolloverStudent(an, "promote"), RolloverStudent(binh, "retain"), RolloverStudent(chi, "transfer")])]
    r = commit(ADMIN, CommitRollover(y.id, "2027-2028", plan, activate_target=True))
    assert (r["promote"], r["retain"], r["transfer"], sorted(r["classes_created"])) == (1, 1, 1, ["10A1", "11A1"])
    new = {c.name: c for c in classes.of_year(r["target_year_id"])}
    assert classes.of(new["11A1"].id) == {an} and classes.of(new["10A1"].id) == {binh} and new["11A1"].grade == 11
    assert classes.members[(k10.id, an)] == "promoted" and classes.members[(k10.id, chi)] == "transferred"
    assert years.rows[r["target_year_id"]].status == "active" and years.rows[y.id].status == "closed"
    again = commit(ADMIN, CommitRollover(y.id, "2027-2028", plan))
    assert again["classes_created"] == [] and classes.of(new["11A1"].id) == {an}
    with pytest.raises(Invalid):
        commit(ADMIN, CommitRollover(y.id, "2025-2026", plan))
    with pytest.raises(Forbidden):
        commit(TEACHER, CommitRollover(y.id, "2027-2028", plan))


def test_levels_and_grades_guards_and_class_cache(ports):
    years, classes, grades, levels, audit, cal, uow = ports
    create_level = CreateLevelHandler(levels, audit, uow)
    thpt = create_level(ADMIN, CreateLevel("THPT", "Trung học phổ thông", 10, 12))
    assert thpt.code == "thpt"
    with pytest.raises(Invalid) as e:
        create_level(ADMIN, CreateLevel("x", "X", 12, 13))
    assert "trùng" in e.value.message
    with pytest.raises(Conflict):
        create_level(ADMIN, CreateLevel("thpt", "Lặp", 1, 2))
    create_grade = CreateGradeHandler(levels, grades, audit, uow)
    g10 = create_grade(ADMIN, CreateGrade(10, thpt.id))
    assert g10.name == "Lớp 10"
    with pytest.raises(Invalid):
        create_grade(ADMIN, CreateGrade(7, thpt.id))
    with pytest.raises(Conflict):
        create_grade(ADMIN, CreateGrade(10, thpt.id))
    k = CreateClassHandler(years, classes, grades, audit, cal, uow)(ADMIN, CreateClass("10A1", grade=10))
    assert k.grade_id == g10.id
    UpdateGradeHandler(levels, grades, classes, audit, uow)(ADMIN, UpdateGrade(g10.id, level=11))
    assert classes.rows[k.id].grade == 11  # the classes' cache follows
    with pytest.raises(Conflict) as e:
        DeleteLevelHandler(levels, audit, uow)(ADMIN, DeleteLevel(thpt.id))
    assert e.value.message == "Cấp học còn 1 khối"
