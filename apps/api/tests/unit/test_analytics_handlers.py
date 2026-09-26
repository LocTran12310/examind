"""Analytics handlers against in-memory ports: mastery (its one weak rule, decay, replay and weekly snapshot),
reports, personal review exams and the audit history (no database, no HTTP — architecture-refactor ADR-02)."""
from datetime import UTC, datetime, time, timedelta, timezone
import uuid

import pytest

from app.modules.analytics.application.commands.assign_class_review import AssignClassReview, AssignClassReviewHandler
from app.modules.analytics.application.commands.rebuild_mastery import RebuildMastery, RebuildMasteryHandler
from app.modules.analytics.application.commands.record_answer import RecordAnswer, RecordAnswerHandler
from app.modules.analytics.application.commands.snapshot_week import (
    BackfillWeeks,
    BackfillWeeksHandler,
    SnapshotWeek,
    SnapshotWeekHandler,
    WeeklySnapshot,
)
from app.modules.analytics.application.commands.start_practice import StartPractice, StartPracticeHandler
from app.modules.analytics.application.common import PracticePlanner
from app.modules.analytics.application.dto import ReportFilters
from app.modules.analytics.application.queries.class_overview import ClassOverview, ClassOverviewHandler
from app.modules.analytics.application.queries.group_stats import GroupStats, GroupStatsHandler
from app.modules.analytics.application.queries.heatmap import Heatmap, HeatmapHandler
from app.modules.analytics.application.queries.my_mastery import MyMasteryHandler
from app.modules.analytics.application.queries.my_practice import MyPracticeHandler
from app.modules.analytics.application.queries.student_mastery import StudentMastery, StudentMasteryHandler
from app.modules.analytics.application.queries.topic_stats import TopicStats, TopicStatsHandler
from app.modules.analytics.application.queries.weekly_mastery import (
    MyWeeklyMasteryHandler,
    StudentWeeklyMastery,
    StudentWeeklyMasteryHandler,
)
from app.modules.analytics.domain.services.mastery import HALF_LIFE, MIN_ANSWERS, START, WEAK_BELOW, decay, step, weak_topics
from app.modules.analytics.domain.services.practice import plan_summary, target_difficulties
from app.modules.analytics.domain.services.weeks import week_start
from app.modules.analytics.domain.value_objects import AnswerRecord, Member, PracticeAttempt, ReviewStatus, TopicNode
from app.modules.audit.application.dto import AuditRow
from app.modules.audit.application.queries.search_audit import SearchAudit, SearchAuditHandler
from app.modules.audit.domain.entities import AuditEntry
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest
from app.shared.domain.errors import Conflict, Forbidden, Invalid, NotFound
from tests.unit.fakes import FakeUow

ORG = uuid.uuid4()
NOW = datetime(2026, 9, 22, 8, 0, tzinfo=UTC)
TEACHER = Actor(user_id=uuid.uuid4(), org_id=ORG, role="teacher")
STUDENT = Actor(user_id=uuid.uuid4(), org_id=ORG, role="student")
BOSS = Actor(user_id=uuid.uuid4(), org_id=ORG, role="org_admin")

# a small tree: Đại số › {Mệnh đề, Tập hợp}, Hình học (a strand without children)
ALG = TopicNode(uuid.uuid4(), None, "Đại số", "a")
GEO = TopicNode(uuid.uuid4(), None, "Hình học", "g")
PROP = TopicNode(uuid.uuid4(), ALG.id, "Mệnh đề", "a.p")
SETS = TopicNode(uuid.uuid4(), ALG.id, "Tập hợp", "a.s")
TREE = {t.id: t for t in (ALG, PROP, SETS, GEO)}


class FakeMastery:
    def __init__(self):
        self.rows = {}

    def get(self, student_id, topic_id):
        return self.rows.get((student_id, topic_id))

    def add(self, row):
        self.rows[(row.student_id, row.topic_id)] = row

    def leaves(self, org_id, student_id):
        return [(m, TREE[t]) for (s, t), m in self.rows.items() if s == student_id and m.organization_id == org_id]

    def clear(self, org_id):
        self.rows = {k: m for k, m in self.rows.items() if org_id and m.organization_id != org_id}

    def empty(self):
        return not self.rows

    def flush(self):
        pass


class FakeWeeks:
    def __init__(self):
        self.rows = {}

    def put(self, row):
        self.rows[(row.student_id, row.topic_id, row.week_start)] = row

    def clear(self, org_id, week_start=None):
        def keep(r):
            return (bool(org_id) and r.organization_id != org_id) or (week_start is not None and r.week_start != week_start)

        self.rows = {k: r for k, r in self.rows.items() if keep(r)}

    def series(self, org_id, student_id):
        rows = [r for r in self.rows.values() if r.organization_id == org_id and r.student_id == student_id]
        return sorted(rows, key=lambda r: (r.week_start, str(r.topic_id)))

    def empty(self):
        return not self.rows


class FakeCalendar:
    """Business days in the fixed +07:00 zone, without the settings behind TzCalendar."""

    TZ = timezone(timedelta(hours=7))

    def __init__(self, now=None):
        self.now = now or NOW

    def today(self):
        return self.day_of(self.now)

    def day_of(self, when):
        return when.astimezone(self.TZ).date() if isinstance(when, datetime) else when

    def start_of(self, day):
        return datetime.combine(day, time.min, tzinfo=self.TZ).astimezone(UTC)


class FakeTopics:
    def id_by_path(self, org_id, path):
        return next((t.id for t in TREE.values() if t.path == path), None) if org_id == ORG else None

    def of_org(self, org_id):
        return dict(TREE) if org_id == ORG else {}

    def get(self, topic_id):
        return TREE.get(topic_id)

    def strands(self, org_id, subject_id):
        return [t for t in TREE.values() if t.parent_id is None]


class FakeHistory:
    def __init__(self, answers=(), recent=(), mistakes=()):
        self.answers, self.recent, self.mistakes = list(answers), set(recent), list(mistakes)

    def recent_correct(self, org_id, student_id, since):
        return set(self.recent)

    def mistakes_to_reask(self, org_id, student_id, before, limit):
        return self.mistakes[:limit]

    def replay(self, org_id):
        return [a for a in self.answers if org_id is None or a.organization_id == org_id]

    def empty(self):
        return not self.answers


class FakePool:
    """`n` usable questions per leaf topic ("th"), a few without a topic."""

    def __init__(self, per_topic=10, loose=5):
        self.by_path = {t.path: [(uuid.uuid4(), "th") for _ in range(per_topic)] for t in (PROP, SETS, GEO)}
        self.loose = [(uuid.uuid4(), None) for _ in range(loose)]

    def pool(self, org_id, topic_path, exclude, subject_id=None):
        if topic_path is None:
            rows = [r for rs in self.by_path.values() for r in rs] + self.loose
        else:
            rows = [r for p, rs in self.by_path.items() if p == topic_path or p.startswith(topic_path + ".") for r in rs]
        return [r for r in rows if r[0] not in exclude]


class FakeRoster:
    def __init__(self, members=()):
        self.members = list(members)

    def class_members(self, actor, class_id):
        if class_id != KLASS:
            raise NotFound("Không tìm thấy lớp")
        return list(self.members)

    def is_member(self, org_id, user_id):
        return org_id == ORG and any(m.id == user_id for m in self.members)

    def person(self, user_id):
        return next((m for m in self.members if m.id == user_id), None)


class FakeAssessment:
    def __init__(self):
        self.exams, self.attempts, self.assigned = {}, [], []
        self.practice, self.reviews = [], {}

    def create_exam(self, org_id, title, created_by, adaptive, question_ids, subject_id=None):
        exam_id = uuid.uuid4()
        # the subject is kept like the real adapter keeps it: a fact recorded at build time, not read back later
        self.exams[exam_id] = {"title": title, "adaptive": adaptive, "questions": list(question_ids),
                               "created_by": created_by, "subject_id": subject_id}
        return exam_id

    def start_attempt(self, org_id, exam_id, student_id, deadline):
        self.attempts.append((exam_id, student_id, deadline))
        return uuid.uuid4()

    def assign(self, org_id, exam_id, student_id, title, open_at, close_at, duration_minutes, created_by):
        self.assigned.append((exam_id, student_id, title, duration_minutes))
        return uuid.uuid4()

    def practice_attempts(self, org_id, student_id, limit):
        # keyed by student, like the real reader: the handler passes actor.user_id, and a fake that ignored it
        # would answer a teacher with a student's history and hide exactly the thing worth asserting
        return [a for who, a in self.practice if who == student_id][:limit]

    def latest_review(self, org_id, student_id):
        return self.reviews.get(student_id)


KLASS = uuid.uuid4()


def answer(topic: TopicNode | None, ratio: float, difficulty="th", student=STUDENT.user_id, minutes=0, days=0) -> AnswerRecord:
    return AnswerRecord(ORG, student, topic.path if topic else None, ratio, difficulty, NOW + timedelta(days=days, minutes=minutes))


def enough_answers(topic: TopicNode, ratio: float, n: int = MIN_ANSWERS, first=0, **kw) -> list[AnswerRecord]:
    """`n` answers on one topic a minute apart — the evidence the weak rule asks for (A-03)."""
    return [answer(topic, ratio, minutes=first + i, **kw) for i in range(n)]


def recorded(*answers: AnswerRecord) -> FakeMastery:
    mastery = FakeMastery()
    for a in answers:
        RecordAnswerHandler(mastery, FakeTopics(), FakeUow())(RecordAnswer(a))
    return mastery


def snapshot(weeks, history, now=None) -> WeeklySnapshot:
    return WeeklySnapshot(weeks, FakeTopics(), history, FakeCalendar(now), lambda: now or NOW, FakeUow())


def planner(mastery=None, history=None, pool=None) -> PracticePlanner:
    return PracticePlanner(mastery or FakeMastery(), FakeTopics(), history or FakeHistory(), pool or FakePool(), lambda: NOW)


# ------------------------------------------------------------------ mastery

def test_an_answer_moves_the_topic_mastery_and_unknown_topics_are_ignored():
    mastery, uow = FakeMastery(), FakeUow()
    record = RecordAnswerHandler(mastery, FakeTopics(), uow)
    record(RecordAnswer(answer(PROP, 1.0)))
    record(RecordAnswer(answer(PROP, 0.0, "vdc", minutes=1)))
    record(RecordAnswer(answer(None, 1.0)))
    record(RecordAnswer(AnswerRecord(ORG, STUDENT.user_id, "zz.unknown", 1.0, "th", NOW)))
    row = mastery.get(STUDENT.user_id, PROP.id)
    assert list(mastery.rows) == [(STUDENT.user_id, PROP.id)]
    later = NOW + timedelta(minutes=1)  # the minute between the two answers decays the first one a little (ADR-04)
    assert row.answers == 2 and row.last_at == later
    assert row.mastery == step(step(START, 1.0, "th"), 0.0, "vdc", NOW, later)


def test_mastery_decays_halfway_back_to_the_middle_after_a_half_life():
    assert decay(1.0, NOW, NOW + HALF_LIFE) == 0.75  # halfway from 1.0 back toward 0.5
    assert decay(0.1, NOW, NOW + 2 * HALF_LIFE) == 0.4
    assert decay(0.9, NOW, NOW) == 0.9 and decay(0.9, None, NOW) == 0.9  # no idle time, no clock: untouched
    # the idle time is spent before the answer lands, so a long break softens what one answer can prove
    assert step(1.0, 1.0, "th", NOW, NOW + HALF_LIFE) == round(0.75 + 0.3 * 0.25, 6)
    row = recorded(answer(PROP, 1.0)).get(STUDENT.user_id, PROP.id)
    rows = MyMasteryHandler(recorded(answer(PROP, 1.0)), FakeTopics(), lambda: NOW + HALF_LIFE)(STUDENT)
    assert rows[1]["mastery"] == round(decay(row.mastery, row.last_at, NOW + HALF_LIFE), 4)


def test_a_topic_is_weak_only_below_the_threshold_and_with_enough_answers():
    thin = recorded(*enough_answers(GEO, 0.0, MIN_ANSWERS - 1))
    rows = MyMasteryHandler(thin, FakeTopics(), lambda: NOW)(STUDENT)
    geo = next(r for r in rows if r["path"] == "g")
    assert geo["mastery"] < WEAK_BELOW and geo["answers"] == MIN_ANSWERS - 1
    assert geo["enough_data"] is False and geo["weak"] is False and weak_topics(rows) == []

    mastery = recorded(*enough_answers(PROP, 0.0), *enough_answers(SETS, 1.0), *enough_answers(GEO, 0.0, MIN_ANSWERS - 1))
    rows = MyMasteryHandler(mastery, FakeTopics(), lambda: NOW)(STUDENT)
    assert [r["name"] for r in weak_topics(rows)] == ["Mệnh đề"]  # Tập hợp is strong, Hình học has too little behind it
    assert {r["name"]: (r["enough_data"], r["weak"]) for r in rows if r["tracked"]} == {
        "Mệnh đề": (True, True), "Tập hợp": (True, False), "Hình học": (False, False)}


def test_rebuild_replays_every_fact_for_an_org_admin_only():
    answers = [answer(PROP, 1.0), answer(SETS, 0.0, "nb", minutes=1), answer(PROP, 0.5, minutes=2), answer(None, 1.0, minutes=3)]
    live = recorded(*answers)
    rebuilt = FakeMastery()
    rebuilt.add(live.get(STUDENT.user_id, PROP.id))  # stale rows are cleared first
    uow = FakeUow()
    handle = RebuildMasteryHandler(rebuilt, FakeTopics(), FakeHistory(answers), uow)
    out = handle(BOSS, RebuildMastery())
    assert vars(out) == {"students": 1, "topics": 2, "facts": 4} and uow.commits == 1
    assert {k: (m.mastery, m.answers) for k, m in rebuilt.rows.items()} == {k: (m.mastery, m.answers) for k, m in live.rows.items()}
    for who in (TEACHER, STUDENT):
        with pytest.raises(Forbidden):
            handle(who, RebuildMastery())


def test_my_mastery_rolls_leaves_up_the_tree_and_answers_whoever_asks_about_themselves():
    mastery = recorded(answer(PROP, 0.0), answer(SETS, 1.0), answer(SETS, 1.0))
    rows = MyMasteryHandler(mastery, FakeTopics(), lambda: NOW)(STUDENT)
    assert [r["path"] for r in rows] == ["a", "a.p", "a.s"]
    parent = rows[0]
    assert parent["tracked"] is False and parent["answers"] == 3 and parent["depth"] == 1
    p, s = mastery.get(STUDENT.user_id, PROP.id), mastery.get(STUDENT.user_id, SETS.id)
    assert parent["mastery"] == round((p.mastery * 1 + s.mastery * 2) / 3, 4)
    # roles nest (exam-runner-and-roles ADR-02): a teacher asking for their own rows gets their own, which is
    # empty. Reading a student's is a different question and has its own handler.
    assert MyMasteryHandler(mastery, FakeTopics(), lambda: NOW)(TEACHER) == []


def test_staff_read_a_member_s_mastery_only():
    member = Member(STUDENT.user_id, "An", "hs01", role="student")
    handle = StudentMasteryHandler(FakeMastery(), FakeTopics(), FakeRoster([member]), lambda: NOW)
    assert handle(TEACHER, StudentMastery(STUDENT.user_id)) == []
    with pytest.raises(NotFound):
        handle(TEACHER, StudentMastery(uuid.uuid4()))


# ------------------------------------------------------------------ the weekly snapshot

LATER = NOW + timedelta(days=20)  # every week of the fixtures below has closed by then


def test_the_weekly_snapshot_holds_where_each_week_ended_and_what_it_saw():
    answers = [*enough_answers(PROP, 0.0, 2), *enough_answers(SETS, 1.0, 3, days=14)]
    weeks = FakeWeeks()
    written = BackfillWeeksHandler(snapshot(weeks, FakeHistory(answers), LATER))(BackfillWeeks())
    series = MyWeeklyMasteryHandler(weeks)(STUDENT)["weeks"]
    monday = week_start(FakeCalendar().day_of(NOW))
    assert [w["week_start"] for w in series] == [monday + timedelta(days=7 * i) for i in range(4)]
    assert written == 1 + 1 + 2 + 2  # Mệnh đề alone, again in the silent week, then both, then both again
    assert [(t["topic_id"], t["answers"]) for t in series[0]["topics"]] == [(PROP.id, 2)]
    assert [t["answers"] for t in series[1]["topics"]] == [0]  # a week nobody answered in still holds a value
    assert series[1]["topics"][0]["mastery"] > series[0]["topics"][0]["mastery"]  # decayed back toward the middle
    assert {t["topic_id"]: t["answers"] for t in series[2]["topics"]} == {PROP.id: 0, SETS.id: 3}


def test_the_weekly_job_writes_the_running_week_and_matches_the_backfill():
    answers = enough_answers(PROP, 0.0, 3)
    backfilled, live = FakeWeeks(), FakeWeeks()
    BackfillWeeksHandler(snapshot(backfilled, FakeHistory(answers)))(BackfillWeeks())
    assert SnapshotWeekHandler(snapshot(live, FakeHistory(answers)), FakeCalendar())(SnapshotWeek()) == 1
    assert {k: vars(r) for k, r in live.rows.items()} == {k: vars(r) for k, r in backfilled.rows.items()}
    row = next(iter(live.rows.values()))
    assert row.mastery == recorded(*answers).get(STUDENT.user_id, PROP.id).mastery  # the week is still running: no decay yet
    assert BackfillWeeksHandler(snapshot(FakeWeeks(), FakeHistory()))(BackfillWeeks()) == 0  # no facts, no weeks


def test_the_weekly_series_is_the_student_s_own_or_a_member_s():
    weeks, member = FakeWeeks(), Member(STUDENT.user_id, "An", "hs01", role="student")
    BackfillWeeksHandler(snapshot(weeks, FakeHistory(enough_answers(PROP, 0.0, 2))))(BackfillWeeks())
    mine = MyWeeklyMasteryHandler(weeks)(STUDENT)
    assert StudentWeeklyMasteryHandler(weeks, FakeRoster([member]))(TEACHER, StudentWeeklyMastery(STUDENT.user_id)) == mine
    assert MyWeeklyMasteryHandler(weeks)(TEACHER)["weeks"] == []
    with pytest.raises(NotFound):
        StudentWeeklyMasteryHandler(weeks, FakeRoster([member]))(TEACHER, StudentWeeklyMastery(uuid.uuid4()))


# ------------------------------------------------------------------ reports

class FakeReports:
    def __init__(self):
        self.scopes = []

    def topics(self, scope, subject_id):
        self.scopes.append(scope)
        return [{"id": ALG.id, "parent_id": None, "name": ALG.name, "path": "a", "depth": 1, "level_kind": "strand",
                 "points": 1.5, "max_points": 2.0, "answered": 8}]

    def unclassified(self, scope):
        return {"p": 0.25, "m": 1.0, "n": 4}

    def groups(self, scope, by):
        self.scopes.append(scope)
        return [{"key": "mcq", "label": "mcq", "p": 1.0, "m": 2.0, "n": 8}, {"key": "essay", "label": "essay", "p": 0, "m": 0, "n": 1},
                {"key": "true_false", "label": "true_false", "p": 0.2, "m": 1.0, "n": 1}]

    def heat(self, scope, level, subject_id):
        self.scopes.append((scope, level))
        return [{"student_id": STUDENT.user_id, "topic_id": ALG.id, "name": ALG.name, "path": "a", "p": 1, "m": 4, "n": 4}]

    def class_students(self, org_id, class_id):
        return [{"id": STUDENT.user_id, "full_name": "An", "username": "hs01"}, {"id": uuid.uuid4(), "full_name": "Bình", "username": "hs02"}]


def test_students_only_ever_read_their_own_facts():
    reader = FakeReports()
    rows = TopicStatsHandler(reader)(STUDENT, TopicStats(ReportFilters(student_id=uuid.uuid4())))
    assert reader.scopes[0].filters.student_id == STUDENT.user_id and reader.scopes[0].org_id == ORG
    assert rows[0]["ratio"] == 0.75
    # subject_id là None: hàng này gom đúng những câu không có chuyên đề, nên nó không có môn nào để nhận
    assert rows[-1] == {"id": None, "parent_id": None, "name": "Chưa phân loại", "path": "", "depth": 1, "level_kind": "strand",
                        "subject_id": None, "points": 0.25, "max_points": 1.0, "answered": 4, "ratio": 0.25}
    with pytest.raises(Forbidden):
        TopicStatsHandler(reader)(Actor(uuid.uuid4(), ORG, "super_admin"), TopicStats())


def test_groups_weakest_first_and_an_unknown_grouping_is_invalid():
    rows = GroupStatsHandler(FakeReports())(TEACHER, GroupStats("type"))
    assert [g["key"] for g in rows] == ["true_false", "mcq", "essay"] and rows[-1]["ratio"] is None
    with pytest.raises(Invalid):
        GroupStatsHandler(FakeReports())(TEACHER, GroupStats("bogus"))


def test_heatmap_lists_every_student_of_the_class_for_staff():
    reader = FakeReports()
    hm = HeatmapHandler(reader)(TEACHER, Heatmap(KLASS, level=9, term_code="hk1"))
    scope, level = reader.scopes[0]
    assert level == 4 and scope.filters.class_id == KLASS and scope.filters.term_code == "hk1"
    assert hm["columns"] == [{"id": ALG.id, "name": ALG.name, "path": "a"}]
    assert [r["username"] for r in hm["rows"]] == ["hs01", "hs02"]
    assert hm["rows"][0]["cells"] == {str(ALG.id): {"ratio": 0.25, "answered": 4}} and hm["rows"][1]["cells"] == {}
    with pytest.raises(Forbidden):
        HeatmapHandler(reader)(STUDENT, Heatmap(KLASS))


# ------------------------------------------------------------------ personal review exams

def test_a_plan_without_history_is_balanced_over_the_strands():
    plan = planner().build(ORG, STUDENT.user_id, count=10, seed=1)
    assert len(plan.picks) == 10 and len(plan.ids()) == 10 and plan.note.startswith("Chưa có dữ liệu")
    assert {p.reason for p in plan.picks} <= {"Làm quen", "Bổ sung"} and {p.topic for p in plan.picks if p.topic} == {"Đại số", "Hình học"}


def test_a_plan_targets_weak_topics_reasks_old_mistakes_and_skips_recent_right_answers():
    mastery = recorded(*enough_answers(PROP, 0.0), *enough_answers(SETS, 0.4, first=10))
    pool = FakePool()
    recent = {pool.by_path["a.p"][0][0]}
    mistakes = [pool.by_path["a.s"][1][0], pool.by_path["a.s"][2][0], pool.by_path["a.s"][3][0]]
    plan = planner(mastery, FakeHistory(recent=recent, mistakes=mistakes), pool).build(ORG, STUDENT.user_id, count=20, seed=3)
    reasons = [p.reason for p in plan.picks]
    assert len(plan.picks) == 20 and len(plan.ids()) == 20 and not (plan.ids() & recent)
    assert reasons.count("Ôn lại câu từng làm sai") == 2  # 10 % of 20
    weak = [p for p in plan.picks if p.reason == "Chuyên đề yếu"]
    assert weak and weak[0].topic == "Mệnh đề"  # the weakest topic comes first
    assert target_difficulties(0.2) == ["nb", "th"] and target_difficulties(0.9) == ["vd", "vdc"]


def test_a_plan_is_never_built_around_a_topic_with_too_little_behind_it():
    thin = recorded(*enough_answers(PROP, 0.0, MIN_ANSWERS - 1))
    plan = planner(thin, pool=FakePool()).build(ORG, STUDENT.user_id, count=10, seed=1)
    assert len(plan.picks) == 10 and "Chưa đủ dữ liệu theo chuyên đề" in plan.note
    assert {p.reason for p in plan.picks} <= {"Làm quen", "Bổ sung"}  # no "Chuyên đề yếu" on two answers
    enough = recorded(*enough_answers(PROP, 0.0))
    assert any(p.reason == "Chuyên đề yếu" for p in planner(enough, pool=FakePool()).build(ORG, STUDENT.user_id, count=10, seed=1).picks)


def test_start_practice_creates_the_exam_and_an_hour_long_attempt():
    me = Member(STUDENT.user_id, "An", "hs01", role="student")
    assessment, uow = FakeAssessment(), FakeUow()
    handle = StartPracticeHandler(planner(), assessment, FakeRoster([me]), lambda: NOW, uow)
    out = handle(STUDENT, StartPractice(count=3))  # at least 5 questions
    exam = next(iter(assessment.exams.values()))
    assert out["question_count"] == 5 == len(exam["questions"]) and uow.commits == 1
    assert exam["title"] == "Đề ôn tập – An" and exam["adaptive"]["student_id"] == str(STUDENT.user_id)
    assert assessment.attempts[0][2] == NOW + timedelta(minutes=60)
    assert out["groups"] == plan_summary({"adaptive": exam["adaptive"]})["groups"] and out["note"] == exam["adaptive"]["note"]
    assert exam["subject_id"] is None  # asked without a subject: the exam records none rather than guessing
    # asked inside one, the exam keeps it — the plan was drawn there, so it is a fact and not an inference
    subject = uuid.uuid4()
    handle(STUDENT, StartPractice(count=3, subject_id=subject))
    assert [e["subject_id"] for e in assessment.exams.values()][-1] == subject
    with pytest.raises(Forbidden):
        handle(TEACHER, StartPractice())
    empty = StartPracticeHandler(planner(pool=FakePool(per_topic=0, loose=0)), assessment, FakeRoster([me]), lambda: NOW, uow)
    with pytest.raises(Conflict) as e:
        empty(STUDENT, StartPractice())
    assert e.value.code == "empty_bank"


def test_a_class_review_gives_each_active_student_an_own_exam():
    members = [Member(uuid.uuid4(), "An", "hs01", True, "student"), Member(uuid.uuid4(), "Bình", "hs02", False, "student"),
               Member(uuid.uuid4(), "Cô Lan", "gv01", True, "teacher"), Member(uuid.uuid4(), "Chi", "hs03", True, "student")]
    assessment, uow = FakeAssessment(), FakeUow()
    handle = AssignClassReviewHandler(planner(), assessment, FakeRoster(members), uow)
    n = handle(TEACHER, AssignClassReview(KLASS, NOW, NOW + timedelta(days=1), count=10))
    assert n == 2 and uow.commits == 1
    assert [(s, t) for _, s, t, _ in assessment.assigned] == [(members[0].id, "Đề ôn cá nhân"), (members[3].id, "Đề ôn cá nhân")]
    assert sorted(e["title"] for e in assessment.exams.values()) == ["Đề ôn cá nhân – An", "Đề ôn cá nhân – Chi"]
    with pytest.raises(Invalid) as e:
        handle(TEACHER, AssignClassReview(KLASS, NOW, NOW))
    assert e.value.fields == {"close_at": "Thời gian đóng phải sau thời gian mở"}
    with pytest.raises(Invalid):
        handle(TEACHER, AssignClassReview(KLASS, NOW, NOW + timedelta(hours=1), duration_minutes=0))
    with pytest.raises(NotFound):
        handle(TEACHER, AssignClassReview(uuid.uuid4(), NOW, NOW + timedelta(hours=1)))


def test_class_overview_and_practice_history():
    student = Member(STUDENT.user_id, "An", "hs01", True, "student")
    mastery = recorded(*enough_answers(PROP, 0.0), *enough_answers(SETS, 0.4, first=10),
                       *enough_answers(GEO, 0.0, MIN_ANSWERS - 1, first=20))
    assessment = FakeAssessment()
    assessment.reviews[student.id] = ReviewStatus(uuid.uuid4(), "Đề ôn cá nhân", "not_started", NOW, NOW + timedelta(days=7), 3)
    teacher = Member(uuid.uuid4(), "Cô Lan", "gv01", True, "teacher")
    ov = ClassOverviewHandler(mastery, FakeTopics(), FakeRoster([student, teacher]), assessment, lambda: NOW)(TEACHER, ClassOverview(KLASS))
    assert [o["username"] for o in ov] == ["hs01"]
    assert [w["name"] for w in ov[0]["weakest"]] == ["Mệnh đề", "Tập hợp"]  # Hình học has too little behind it
    # the cell has to say which paper, when it was given, by when, and that it is not the only one (ADR-02)
    assert ov[0]["review"]["status"] == "not_started" and ov[0]["review"]["title"] == "Đề ôn cá nhân"
    assert ov[0]["review"]["close_at"] == NOW + timedelta(days=7) and ov[0]["review"]["total"] == 3

    settings = {"adaptive": {"note": None, "plan": [{"question_id": "q1", "reason": "Chuyên đề yếu", "topic": "Mệnh đề"},
                                                    {"question_id": "q2", "reason": "Chuyên đề yếu", "topic": "Mệnh đề"},
                                                    {"question_id": "q3", "reason": "Bổ sung", "topic": None}]}}
    assessment.practice = [(STUDENT.user_id, PracticeAttempt(uuid.uuid4(), "Đề ôn tập – An", "submitted", NOW, NOW, 7.5, settings))]
    history = MyPracticeHandler(assessment)(STUDENT)
    assert history[0]["score10"] == 7.5 and history[0]["groups"] == [{"reason": "Chuyên đề yếu", "topic": "Mệnh đề", "count": 2},
                                                                      {"reason": "Bổ sung", "topic": None, "count": 1}]
    # roles nest, so a teacher may ask — and is answered about themselves, not about the student (ADR-02)
    assert MyPracticeHandler(assessment)(TEACHER) == []


# ------------------------------------------------------------------ audit history

class FakeAuditReader:
    def __init__(self):
        self.calls = []

    def search(self, org_id, req, related=None, target_id=None, organization_id=None):
        self.calls.append((org_id, related, target_id))
        e = AuditEntry(organization_id=ORG, action="class.create", target_type="class")
        return Page([AuditRow(e, "Quản Trị", "trungtama")], 1, req.page, req.limit)


def test_history_is_for_org_admins_and_the_platform_admin_sees_every_org():
    reader = FakeAuditReader()
    handle = SearchAuditHandler(reader)
    target = uuid.uuid4()
    page = handle(Actor(uuid.uuid4(), ORG, "org_admin"), SearchAudit(SearchRequest(), target_id=target))
    assert page.total == 1 and reader.calls[-1] == (ORG, None, target)
    handle(Actor(uuid.uuid4(), ORG, "super_admin", is_super=True), SearchAudit(SearchRequest()))
    assert reader.calls[-1][0] is None
    handle(Actor(uuid.uuid4(), ORG, "org_admin", is_super=True), SearchAudit(SearchRequest()))  # a super admin inside one org
    assert reader.calls[-1][0] == ORG
    with pytest.raises(Forbidden):
        handle(TEACHER, SearchAudit(SearchRequest()))
