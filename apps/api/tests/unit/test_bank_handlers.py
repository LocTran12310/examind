"""Bank handlers against in-memory ports: writing, bulk, review, answer keys, key audit, triage, item statistics (ADR-02)."""
from dataclasses import replace
import uuid

import pytest

from app.modules.bank.application.commands.apply_answer_key import ApplyAnswerKey, ApplyAnswerKeyHandler
from app.modules.bank.application.commands.approve_confident import ApproveConfident, ApproveConfidentHandler
from app.modules.bank.application.commands.assign_reviewer import AssignReviewer, AssignReviewerHandler
from app.modules.bank.application.commands.audit_keys import AuditKeys, AuditKeysHandler
from app.modules.bank.application.commands.bulk_update_questions import BulkUpdateQuestions, BulkUpdateQuestionsHandler
from app.modules.bank.application.commands.create_question import CreateQuestion, CreateQuestionHandler
from app.modules.bank.application.commands.delete_question import DeleteQuestion, DeleteQuestionHandler
from app.modules.bank.application.commands.review_question import ReviewQuestion, ReviewQuestionHandler
from app.modules.bank.application.commands.triage_questions import TriageQuestions, TriageQuestionsHandler
from app.modules.bank.application.commands.update_question import UpdateQuestion, UpdateQuestionHandler
from app.modules.bank.application.common import resolve_filters
from app.modules.bank.application.dto import BankFilters, ItemStats, OptionStat, question_view
from app.modules.bank.application.queries.question_stats import QuestionStats, QuestionStatsHandler
from app.modules.bank.application.queries.review_queue import ReviewQueue, ReviewQueueHandler
from app.modules.bank.domain.entities import Question
from app.shared.application.actor import Actor
from app.shared.domain.errors import Conflict, Forbidden, Invalid, NotFound
from tests.unit.fakes import FakeUow

ORG = uuid.uuid4()
DOC = uuid.uuid4()
TEACHER = Actor(user_id=uuid.uuid4(), org_id=ORG, role="teacher")
ADMIN = Actor(user_id=uuid.uuid4(), org_id=ORG, role="org_admin")
TOPIC, SUB_TOPIC, TAG_A, TAG_B, SUBJECT = (uuid.uuid4() for _ in range(5))
OPTS = [{"label": l, "content": c} for l, c in zip("ABCD", "1234")]


class FakeQuestions:
    def __init__(self):
        self.rows: dict = {}
        self.topics: dict = {}
        self.tags: dict = {}
        self.released: list = []

    def get(self, org_id, question_id):
        q = self.rows.get(question_id)
        return q if q is not None and q.organization_id == org_id else None

    def many(self, org_id, ids):
        return [q for i, q in self.rows.items() if i in ids and (org_id is None or q.organization_id == org_id)]

    def review_queue(self, document_id):
        return [q for q in self.rows.values() if q.source_document_id == document_id
                and (q.status in ("needs_review", "flagged") or q.is_spot_pending)]

    def of_document(self, document_id, *, type=None, status=None, spot_check=None):
        return [q for q in self.rows.values() if q.source_document_id == document_id and (type is None or q.type == type)
                and (status is None or q.status == status) and (spot_check is None or q.spot_check == spot_check)]

    def add(self, q):
        self.rows[q.id] = q

    def remove(self, q):
        del self.rows[q.id]

    def release_duplicates_of(self, ids):
        self.released += list(ids)

    def replace_topics(self, question_id, topic_ids, primary_id):
        self.topics[question_id] = (list(topic_ids), primary_id)

    def tag_ids(self, question_id):
        return set(self.tags.get(question_id, []))

    def replace_tags(self, question_id, tag_ids):
        self.tags[question_id] = list(tag_ids)


class FakeLog:
    def __init__(self):
        self.events: list = []

    def record(self, org_id, user_id, question_id, action, before, after):
        self.events.append((question_id, action, before, after))

    def recent_spot_actions(self, org_id, limit):
        return [a for _, a, _, _ in reversed(self.events) if a in ("spot_ok", "spot_fail")][:limit]

    def actions(self, qid=None):
        return [a for q, a, _, _ in self.events if qid is None or q == qid]


class FakeTaxonomy:
    def topic_paths(self, org_id, ids):
        known = {TOPIC: "t1", SUB_TOPIC: "t1.t2"}
        return {i: known[i] for i in ids if org_id == ORG and i in known}

    def tag_groups(self, org_id, ids):
        known = {TAG_A: "source", TAG_B: "method"}
        return {i: known[i] for i in ids if org_id == ORG and i in known}

    def subject_exists(self, org_id, subject_id):
        return org_id == ORG and subject_id == SUBJECT


class FakeSettings:
    def __init__(self, threshold=0.85):
        self.value = threshold

    def threshold(self, org_id):
        return self.value

    def set_threshold(self, org_id, value):
        self.value = value


class FakeViews:
    def views(self, questions, groups=None):
        return [question_view(q, group=(groups or {}).get(q.id)) for q in questions]


class FakeDocuments:
    def __init__(self):
        self.assigned: dict = {}

    def exists(self, org_id, document_id):
        return org_id == ORG and document_id == DOC

    def assign(self, org_id, document_id, user_id):
        self.assigned[document_id] = user_id


@pytest.fixture
def ports():
    return FakeQuestions(), FakeTaxonomy(), FakeLog(), FakeSettings(), FakeViews(), FakeUow()


def parsed(qs: FakeQuestions, **kw) -> Question:
    q = Question(organization_id=ORG, source_document_id=DOC, options=list(OPTS), **kw)
    qs.add(q)
    return q


def test_create_is_approved_and_placed_or_refused_with_blocking_issues(ports):
    qs, tax, log, _, views, uow = ports
    create = CreateQuestionHandler(qs, tax, log, views, uow)
    v = create(TEACHER, CreateQuestion(stem="1 + 1 = ?", options=OPTS, answer={"key": "B"}, primary_topic_id=TOPIC, tag_ids=[TAG_A]))
    assert v.status == "approved" and v.answer_source == "manual" and uow.commits == 1
    assert qs.topics[v.id] == ([TOPIC], TOPIC) and qs.tags[v.id] == [TAG_A]
    assert log.actions(v.id) == ["topic", "edit"]
    with pytest.raises(Invalid) as e:
        create(TEACHER, CreateQuestion(stem="x", options=OPTS))
    assert e.value.code == "has_blocking_issues"
    with pytest.raises(Invalid):
        create(TEACHER, CreateQuestion(stem="x", options=OPTS, answer={"key": "E"}))
    with pytest.raises(Invalid):
        create(TEACHER, CreateQuestion(stem="x", options=OPTS, answer={"key": "A"}, topic_ids=[uuid.uuid4()]))
    with pytest.raises(Invalid):
        create(TEACHER, CreateQuestion(type="poem"))


def test_answer_only_edit_is_recorded_as_answer_and_spot_edit_fails_the_check(ports):
    qs, tax, log, settings, views, uow = ports
    update = UpdateQuestionHandler(qs, tax, log, settings, views, uow)
    q = parsed(qs, stem="Câu hỏi", status="needs_review", issues=["thiếu đáp án"])
    v = update(TEACHER, UpdateQuestion(q.id, answer={"key": "C"}, sent=frozenset({"answer"})))
    assert v.answer == {"key": "C"} and "thiếu đáp án" not in v.issues and v.status == "needs_review"
    assert log.actions(q.id) == ["answer"]
    with pytest.raises(Invalid):
        update(TEACHER, UpdateQuestion(q.id, subject_id=uuid.uuid4(), sent=frozenset({"subject_id"})))
    # two corrected spot checks in a row: auto-approval gets stricter
    for _ in range(2):
        s = parsed(qs, stem="Đúng", answer={"key": "A"}, status="auto_approved", spot_check=True)
        assert update(TEACHER, UpdateQuestion(s.id, solution="Sửa", sent=frozenset({"solution"}))).status == "approved"
    assert log.actions().count("spot_fail") == 2 and settings.value == 0.9 and "triage" in log.actions()


def test_delete_refuses_a_question_in_use_and_releases_duplicates(ports):
    qs, _, log, _, _, uow = ports
    q = parsed(qs, stem="x")

    class Usage:
        used = True

        def in_use(self, qid):
            return self.used

    usage = Usage()
    delete = DeleteQuestionHandler(qs, usage, log, uow)
    with pytest.raises(Conflict) as e:
        delete(TEACHER, DeleteQuestion(q.id))
    assert e.value.code == "question_in_use"
    usage.used = False
    delete(TEACHER, DeleteQuestion(q.id))
    assert q.id not in qs.rows and qs.released == [q.id] and log.events[-1][3] == {"deleted": True}
    with pytest.raises(NotFound):
        delete(TEACHER, DeleteQuestion(q.id))


def test_bulk_is_all_or_nothing(ports):
    qs, tax, log, _, _, uow = ports
    bulk = BulkUpdateQuestionsHandler(qs, tax, log, uow)
    a = parsed(qs, stem="a", answer={"key": "A"}, status="needs_review", issues=["OCR"])
    b = parsed(qs, stem="b", answer={"key": "B"}, status="needs_review")
    qs.tags[b.id] = [TAG_B]
    assert bulk(TEACHER, BulkUpdateQuestions([a.id, b.id], status="approved", difficulty="vd", add_tag_ids=[TAG_A])) == 2
    assert a.status == b.status == "approved" and "OCR" not in a.issues and a.difficulty == "vd"
    assert set(qs.tags[b.id]) == {TAG_A, TAG_B}
    with pytest.raises(NotFound):
        bulk(TEACHER, BulkUpdateQuestions([a.id, uuid.uuid4()], difficulty="nb"))
    with pytest.raises(Invalid):
        bulk(TEACHER, BulkUpdateQuestions([a.id], status="flagged"))
    broken = parsed(qs, stem="", status="needs_review", issues=["thiếu đề bài"], number=7)
    with pytest.raises(Conflict) as e:
        bulk(TEACHER, BulkUpdateQuestions([broken.id], status="approved"))
    assert e.value.message.startswith("Câu 7 còn lỗi")


def test_review_actions_spot_checks_and_restore(ports):
    qs, _, log, settings, views, uow = ports
    act = ReviewQuestionHandler(qs, log, settings, views, uow)
    broken = parsed(qs, stem="x", status="needs_review", issues=["thiếu phương án"])
    with pytest.raises(Conflict) as e:
        act(TEACHER, ReviewQuestion(broken.id, "approve"))
    assert e.value.code == "has_blocking_issues"
    spot = parsed(qs, stem="ok", answer={"key": "A"}, status="auto_approved", spot_check=True)
    assert act(TEACHER, ReviewQuestion(spot.id, "approve")).status == "approved"
    assert log.actions(spot.id) == ["spot_ok"] and spot.reviewed_by == TEACHER.user_id
    flagged = parsed(qs, stem="k", answer={"key": "A"}, status="flagged", issues=["Nghi sai đáp án"], flag_evidence={"answers": 12})
    act(TEACHER, ReviewQuestion(flagged.id, "approve"))
    assert flagged.flag_evidence == {"answers": 12, "dismissed": True, "answers_at_dismiss": 12} and flagged.issues == []
    assert act(TEACHER, ReviewQuestion(broken.id, "reject")).status == "rejected"
    assert act(TEACHER, ReviewQuestion(broken.id, "restore")).status == "needs_review"
    with pytest.raises(Conflict) as e:
        act(TEACHER, ReviewQuestion(broken.id, "restore"))
    assert e.value.code == "invalid_state"
    with pytest.raises(Invalid):
        act(TEACHER, ReviewQuestion(broken.id, "dance"))


def test_queue_groups_problems_first_and_spot_checks_last(ports):
    qs, _, _, _, views, _ = ports
    parsed(qs, stem="s", answer={"key": "A"}, status="auto_approved", spot_check=True, number=1)
    parsed(qs, stem="o", status="needs_review", issues=["OCR"], number=2)
    parsed(qs, stem="m", status="needs_review", issues=["thiếu đáp án"], number=3)
    parsed(qs, stem="done", status="approved", number=4)
    queue = ReviewQueueHandler(qs, FakeDocuments(), views)(TEACHER, ReviewQueue(DOC))
    assert [v.group for v in queue] == ["thiếu đáp án", "OCR", "Kiểm tra ngẫu nhiên"]
    with pytest.raises(NotFound):
        ReviewQueueHandler(qs, FakeDocuments(), views)(TEACHER, ReviewQueue(uuid.uuid4()))


def test_answer_key_and_approve_confident(ports):
    qs, _, log, _, _, uow = ports
    docs = FakeDocuments()
    q1 = parsed(qs, stem="1", number=1, status="needs_review", issues=["thiếu đáp án"])
    q2 = parsed(qs, stem="2", number=2, status="approved", answer={"key": "A"})
    parsed(qs, stem="3", number=3, status="auto_approved", answer={"key": "A"})
    parsed(qs, stem="4", number=4, status="auto_approved", answer={"key": "A"}, spot_check=True)
    r = ApplyAnswerKeyHandler(qs, docs, log, uow)(TEACHER, ApplyAnswerKey(DOC, "1B 2C 9A"))
    assert (r.applied, r.approved, r.unmatched) == (1, 1, [9])
    assert q1.answer == {"key": "B"} and q1.status == "approved" and q2.answer == {"key": "A"}
    assert ApproveConfidentHandler(qs, docs, log, uow)(TEACHER, ApproveConfident(DOC)) == 1
    with pytest.raises(NotFound):
        ApproveConfidentHandler(qs, docs, log, uow)(TEACHER, ApproveConfident(uuid.uuid4()))


def test_assign_reviewer_is_for_the_admin_and_teachers_only():
    docs = FakeDocuments()
    teacher = uuid.uuid4()

    class Staff:
        def is_teacher(self, org_id, user_id):
            return user_id == teacher

    class Reader:
        def document(self, org_id, document_id):
            return docs.assigned.get(document_id)

    assign = AssignReviewerHandler(docs, Staff(), Reader(), FakeUow())
    with pytest.raises(Forbidden):
        assign(TEACHER, AssignReviewer(DOC, teacher))
    with pytest.raises(Invalid):
        assign(ADMIN, AssignReviewer(DOC, uuid.uuid4()))
    assert assign(ADMIN, AssignReviewer(DOC, teacher)) == teacher
    with pytest.raises(NotFound):
        assign(ADMIN, AssignReviewer(uuid.uuid4(), None))


def test_key_audit_flags_a_contradicted_key_once(ports):
    qs, _, log, _, _, uow = ports
    q = parsed(qs, stem="k", answer={"key": "A"}, status="approved")

    class Stats:
        def mcq_answers(self, org_id):
            return {q.id: [({"key": "B"}, 0.9)] * 4 + [({"key": "C"}, 0.3)] * 6}

    audit = AuditKeysHandler(qs, Stats(), log, uow)
    assert audit(AuditKeys(ORG)) == [q.id]
    assert q.status == "flagged" and "Nghi sai đáp án" in q.issues and q.flag_evidence["top_quartile"]["choice"] == "B"
    q.flag_evidence = {**q.flag_evidence, "dismissed": True, "answers_at_dismiss": 10}
    q.status = "approved"
    assert audit(AuditKeys(ORG)) == []  # a teacher confirmed it: wait for ten more answers


def test_triage_duplicates_statuses_and_spot_checks():
    uow = FakeUow()
    fresh = [Question(organization_id=ORG, stem=f"Tính giá trị biểu thức số {i} thật cẩn thận", options=list(OPTS),
                      answer={"key": "A"}, solution="x", confidence=0.95) for i in range(3)]
    fresh.append(Question(organization_id=ORG, stem="Câu thiếu đáp án nhưng đủ dài để so khớp", options=list(OPTS), confidence=0.5))
    dup_of = uuid.uuid4()

    class Finder:
        def similar(self, q, limit=5):
            if "số 0" in q.stem:
                return [(dup_of, 0.95, q.search_text)]
            if "số 1" in q.stem:
                return [(uuid.uuid4(), 0.95, q.search_text.replace("1", "7"))]  # same words, other numbers
            return []

    counts = TriageQuestionsHandler(Finder(), uow)(TriageQuestions(fresh, 0.85, seed="doc"))
    assert (counts.duplicate, counts.auto_approved, counts.needs_review, counts.spot_check) == (1, 2, 1, 1)
    assert fresh[0].status == "duplicate" and fresh[0].duplicate_of == dup_of and fresh[3].status == "needs_review"
    assert sum(q.spot_check for q in fresh) == 1 and all(q.search_text for q in fresh)


def test_filters_resolve_topics_and_group_tags():
    rf = resolve_filters(FakeTaxonomy(), ORG, BankFilters(topic_ids=(TOPIC, SUB_TOPIC), tag_ids=(TAG_A, TAG_B)))
    assert rf.topic_paths == ("t1", "t1.t2") and sorted(len(g) for g in rf.tag_groups) == [1, 1]
    with pytest.raises(Invalid):
        resolve_filters(FakeTaxonomy(), ORG, BankFilters(topic_ids=(uuid.uuid4(),)))
    with pytest.raises(Invalid):
        resolve_filters(FakeTaxonomy(), uuid.uuid4(), BankFilters(tag_ids=(TAG_A,)))


# ------------------------------------------------------------------ item statistics (learning-telemetry ADR-03)

MEASURED = ItemStats(observations=12, correct_ratio=0.5, first_attempt_ratio=0.4, discrimination=0.3, median_seconds=42,
                     options=[OptionStat(label="A", chosen=6, ratio=0.5, is_key=True)])


class FakeItemStats:
    """Measures whatever it is told to; `enough_data` is the handler's decision, never the reader's."""

    def __init__(self, measured: ItemStats):
        self.measured = measured

    def stats(self, org_id, q):
        return self.measured


def test_item_statistics_are_reported_only_with_enough_observations(ports):
    qs = ports[0]
    q = parsed(qs, type="mcq", stem="Câu đủ dữ liệu", answer={"key": "A"}, status="approved")
    assert QuestionStatsHandler(qs, FakeItemStats(MEASURED))(TEACHER, QuestionStats(q.id)) == replace(MEASURED, enough_data=True)
    thin = QuestionStatsHandler(qs, FakeItemStats(ItemStats(observations=9, correct_ratio=1.0, median_seconds=5)))(
        TEACHER, QuestionStats(q.id))
    assert thin == ItemStats(observations=9)  # nothing but the count below the minimum


def test_item_statistics_of_another_organisation_are_not_found(ports):
    qs = ports[0]
    q = parsed(qs, type="mcq", stem="Câu của trung tâm khác", answer={"key": "A"})
    other = Actor(user_id=uuid.uuid4(), org_id=uuid.uuid4(), role="teacher")
    with pytest.raises(NotFound):
        QuestionStatsHandler(qs, FakeItemStats(MEASURED))(other, QuestionStats(q.id))
