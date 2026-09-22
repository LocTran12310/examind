"""Analytics handlers against in-memory ports: mastery, reports, personal review exams and the audit history
(no database, no HTTP — architecture-refactor ADR-02)."""
from datetime import UTC, datetime, timedelta
import uuid

import pytest

from app.modules.analytics.application.commands.assign_class_review import AssignClassReview, AssignClassReviewHandler
from app.modules.analytics.application.commands.rebuild_mastery import RebuildMastery, RebuildMasteryHandler
from app.modules.analytics.application.commands.record_answer import RecordAnswer, RecordAnswerHandler
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
from app.modules.analytics.domain.services.mastery import START, step
from app.modules.analytics.domain.services.practice import plan_summary, target_difficulties
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

    def create_exam(self, org_id, title, created_by, adaptive, question_ids):
        exam_id = uuid.uuid4()
        self.exams[exam_id] = {"title": title, "adaptive": adaptive, "questions": list(question_ids), "created_by": created_by}
        return exam_id

    def start_attempt(self, org_id, exam_id, student_id, deadline):
        self.attempts.append((exam_id, student_id, deadline))
        return uuid.uuid4()

    def assign(self, org_id, exam_id, student_id, title, open_at, close_at, duration_minutes, created_by):
        self.assigned.append((exam_id, student_id, title, duration_minutes))
        return uuid.uuid4()

    def practice_attempts(self, org_id, student_id, limit):
        return self.practice[:limit]

    def latest_review(self, org_id, student_id):
        return self.reviews.get(student_id)


KLASS = uuid.uuid4()


def answer(topic: TopicNode | None, ratio: float, difficulty="th", student=STUDENT.user_id, minutes=0) -> AnswerRecord:
    return AnswerRecord(ORG, student, topic.path if topic else None, ratio, difficulty, NOW + timedelta(minutes=minutes))


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
    assert row.answers == 2 and row.mastery == step(step(START, 1.0, "th"), 0.0, "vdc") and row.last_at == NOW + timedelta(minutes=1)


def test_rebuild_replays_every_fact_and_matches_live_grading():
    answers = [answer(PROP, 1.0), answer(SETS, 0.0, "nb", minutes=1), answer(PROP, 0.5, minutes=2), answer(None, 1.0, minutes=3)]
    live = FakeMastery()
    for a in answers:
        RecordAnswerHandler(live, FakeTopics(), FakeUow())(RecordAnswer(a))
    rebuilt = FakeMastery()
    rebuilt.add(live.get(STUDENT.user_id, PROP.id))  # stale rows are cleared first
    n = RebuildMasteryHandler(rebuilt, FakeTopics(), FakeHistory(answers), FakeUow())(RebuildMastery(ORG))
    assert n == 4
    assert {k: (m.mastery, m.answers) for k, m in rebuilt.rows.items()} == {k: (m.mastery, m.answers) for k, m in live.rows.items()}


def test_my_mastery_rolls_leaves_up_the_tree_and_is_for_students_only():
    mastery = FakeMastery()
    for a in (answer(PROP, 0.0), answer(SETS, 1.0), answer(SETS, 1.0)):
        RecordAnswerHandler(mastery, FakeTopics(), FakeUow())(RecordAnswer(a))
    rows = MyMasteryHandler(mastery, FakeTopics())(STUDENT)
    assert [r["path"] for r in rows] == ["a", "a.p", "a.s"]
    parent = rows[0]
    assert parent["tracked"] is False and parent["answers"] == 3 and parent["depth"] == 1
    p, s = mastery.get(STUDENT.user_id, PROP.id), mastery.get(STUDENT.user_id, SETS.id)
    assert parent["mastery"] == round((p.mastery * 1 + s.mastery * 2) / 3, 4)
    with pytest.raises(Forbidden):
        MyMasteryHandler(mastery, FakeTopics())(TEACHER)


def test_staff_read_a_member_s_mastery_only():
    member = Member(STUDENT.user_id, "An", "hs01", role="student")
    handle = StudentMasteryHandler(FakeMastery(), FakeTopics(), FakeRoster([member]))
    assert handle(TEACHER, StudentMastery(STUDENT.user_id)) == []
    with pytest.raises(NotFound):
        handle(TEACHER, StudentMastery(uuid.uuid4()))


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
    assert rows[-1] == {"id": None, "parent_id": None, "name": "Chưa phân loại", "path": "", "depth": 1, "level_kind": "strand",
                        "points": 0.25, "max_points": 1.0, "answered": 4, "ratio": 0.25}
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
    mastery = FakeMastery()
    for a in (answer(PROP, 0.0), answer(PROP, 0.0), answer(SETS, 1.0)):
        RecordAnswerHandler(mastery, FakeTopics(), FakeUow())(RecordAnswer(a))
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
    mastery = FakeMastery()
    for a in (answer(PROP, 0.0), answer(SETS, 1.0), answer(SETS, 1.0)):
        RecordAnswerHandler(mastery, FakeTopics(), FakeUow())(RecordAnswer(a))
    assessment = FakeAssessment()
    assessment.reviews[student.id] = ReviewStatus(uuid.uuid4(), "Đề ôn cá nhân", "not_started")
    teacher = Member(uuid.uuid4(), "Cô Lan", "gv01", True, "teacher")
    ov = ClassOverviewHandler(mastery, FakeTopics(), FakeRoster([student, teacher]), assessment)(TEACHER, ClassOverview(KLASS))
    assert [o["username"] for o in ov] == ["hs01"]
    assert [w["name"] for w in ov[0]["weakest"]] == ["Mệnh đề", "Tập hợp"] and ov[0]["review"]["status"] == "not_started"

    settings = {"adaptive": {"note": None, "plan": [{"question_id": "q1", "reason": "Chuyên đề yếu", "topic": "Mệnh đề"},
                                                    {"question_id": "q2", "reason": "Chuyên đề yếu", "topic": "Mệnh đề"},
                                                    {"question_id": "q3", "reason": "Bổ sung", "topic": None}]}}
    assessment.practice = [PracticeAttempt(uuid.uuid4(), "Đề ôn tập – An", "submitted", NOW, NOW, 7.5, settings)]
    history = MyPracticeHandler(assessment)(STUDENT)
    assert history[0]["score10"] == 7.5 and history[0]["groups"] == [{"reason": "Chuyên đề yếu", "topic": "Mệnh đề", "count": 2},
                                                                      {"reason": "Bổ sung", "topic": None, "count": 1}]
    with pytest.raises(Forbidden):
        MyPracticeHandler(assessment)(TEACHER)


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
