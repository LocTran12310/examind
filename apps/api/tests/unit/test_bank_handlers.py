"""Bank handlers against in-memory ports: writing, bulk, review, answer keys, key audit, triage, item statistics (ADR-02)."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import uuid

import pytest

from app.modules.bank.application.commands.apply_answer_key import ApplyAnswerKey, ApplyAnswerKeyHandler
from app.modules.bank.application.commands.approve_confident import ApproveConfident, ApproveConfidentHandler
from app.modules.bank.application.commands.assign_reviewer import AssignReviewer, AssignReviewerHandler
from app.modules.bank.application.commands.audit_keys import AuditKeys, AuditKeysHandler
from app.modules.bank.application.commands.bulk_set_topics import BulkSetTopics, BulkSetTopicsHandler
from app.modules.bank.application.commands.bulk_update_questions import BulkUpdateQuestions, BulkUpdateQuestionsHandler
from app.modules.bank.application.commands.create_question import CreateQuestion, CreateQuestionHandler
from app.modules.bank.application.commands.delete_question import DeleteQuestion, DeleteQuestionHandler
from app.modules.bank.application.commands.review_question import ReviewQuestion, ReviewQuestionHandler
from app.modules.bank.application.commands.review_untagged import ReviewUntagged, ReviewUntaggedHandler
from app.modules.bank.application.commands.triage_questions import TriageQuestions, TriageQuestionsHandler
from app.modules.bank.application.commands.undo_batch import UndoBatch, UndoBatchHandler
from app.modules.bank.application.commands.update_question import UpdateQuestion, UpdateQuestionHandler
from app.modules.bank.application.common import resolve_filters
from app.modules.bank.application.dto import BankFilters, ItemStats, OptionStat, question_view
from app.modules.bank.application.queries.question_stats import QuestionStats, QuestionStatsHandler
from app.modules.bank.application.queries.review_queue import ReviewQueue, ReviewQueueHandler
from app.modules.bank.application.queries.search_document_questions import SearchDocumentQuestions, SearchDocumentQuestionsHandler
from app.modules.bank.application.queries.search_question_events import SearchQuestionEvents, SearchQuestionEventsHandler
from app.modules.bank.application.queries.suggest_topics import MAX_QUESTIONS, SuggestTopics, SuggestTopicsHandler
from app.modules.bank.domain.entities import STATUS_KEYS, Question, ReviewEvent
from app.modules.bank.domain.services.history import (
    BLOCKED,
    UNDO_WINDOW,
    UNDONE_BATCH,
    batch_action,
    changed_fields,
    lost_question,
    restore_targets,
    undo_block,
)
from app.modules.bank.domain.services.review import fill_difficulty, pending_count, review_state, waits_for_review
from app.shared.application.actor import Actor
from app.shared.application.search import Page, SearchRequest
from app.shared.domain.errors import Conflict, Forbidden, Invalid, NotFound
from tests.unit.fakes import FakeUow

ORG = uuid.uuid4()
DOC = uuid.uuid4()
TEACHER = Actor(user_id=uuid.uuid4(), org_id=ORG, role="teacher")
ADMIN = Actor(user_id=uuid.uuid4(), org_id=ORG, role="org_admin")
TOPIC, SUB_TOPIC, TAG_A, TAG_B, SUBJECT = (uuid.uuid4() for _ in range(5))
OTHER_SUBJECT, OTHER_TOPIC = uuid.uuid4(), uuid.uuid4()   # a second subject and a topic of its tree
GRADES = {10, 11, 12}
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

    def primary_topic_ids(self, question_ids):
        return {q: primary for q, (_, primary) in self.topics.items() if q in question_ids and primary is not None}

    def topic_ids(self, question_id):
        return self.topics.get(question_id, ([], None))

    def tag_ids(self, question_id):
        return set(self.tags.get(question_id, []))

    def replace_tags(self, question_id, tag_ids):
        self.tags[question_id] = list(tag_ids)


class FakeLog:
    def __init__(self):
        self.events: list = []
        self.at = datetime.now(UTC)  # when the recorded events happened; an undo reads it back to check the window

    def record(self, org_id, user_id, question_id, action, before, after, batch_id=None):
        self.events.append((question_id, action, before, after, batch_id))

    def batch(self, org_id, batch_id):
        return [ReviewEvent(organization_id=org_id, question_id=e[0], action=e[1], before=e[2], after=e[3], batch_id=e[4],
                            created_at=self.at) for e in self.events if e[4] == batch_id]

    def undone_by(self, org_id, batch_id):
        return next((e[4] for e in self.events if e[1] == "undo" and (e[3] or {}).get(UNDONE_BATCH) == str(batch_id)), None)

    def recent_spot_actions(self, org_id, limit):
        return [e[1] for e in reversed(self.events) if e[1] in ("spot_ok", "spot_fail")][:limit]

    def actions(self, qid=None):
        return [e[1] for e in self.events if qid is None or e[0] == qid]

    def batches(self, qid=None):
        return {e[4] for e in self.events if qid is None or e[0] == qid}


class FakeTaxonomy:
    def topic_paths(self, org_id, ids):
        known = {TOPIC: "t1", SUB_TOPIC: "t1.t2", OTHER_TOPIC: "t3"}
        return {i: known[i] for i in ids if org_id == ORG and i in known}

    def topic_labels(self, org_id, ids):
        known = {TOPIC: ("Nguyên hàm", "t1"), SUB_TOPIC: ("Tích phân", "t1.t2"), OTHER_TOPIC: ("Dao động", "t3")}
        return {i: known[i] for i in ids if org_id == ORG and i in known}

    def topic_subjects(self, org_id, ids):
        known = {TOPIC: SUBJECT, SUB_TOPIC: SUBJECT, OTHER_TOPIC: OTHER_SUBJECT}
        return {i: known[i] for i in ids if org_id == ORG and i in known}

    def tag_groups(self, org_id, ids):
        known = {TAG_A: "source", TAG_B: "method"}
        return {i: known[i] for i in ids if org_id == ORG and i in known}

    def subject_exists(self, org_id, subject_id):
        return org_id == ORG and subject_id in (SUBJECT, OTHER_SUBJECT)

    def grade_levels(self, org_id):
        return set(GRADES) if org_id == ORG else set()


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


class FakeReviewReader:
    """The review read model in memory: one document's questions by state, PHẦN then Câu, paged."""

    KEEP = {"pending": waits_for_review,
            "approved": lambda q: q.status in ("approved", "auto_approved") and not waits_for_review(q),
            "rejected": lambda q: q.status == "rejected",
            "duplicate": lambda q: q.status == "duplicate"}

    def __init__(self, questions: FakeQuestions):
        self.questions = questions

    def document_questions(self, org_id, document_id, state, req):
        keep = self.KEEP.get(state)
        rows = sorted((q for q in self.questions.rows.values()
                       if q.organization_id == org_id and q.source_document_id == document_id and (keep is None or keep(q))),
                      key=lambda q: (q.part or "", q.number or 0))
        return Page(rows[req.offset:req.offset + req.limit], len(rows), req.page, req.limit)


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
    assert log.actions(v.id) == ["topic", "tag", "edit"]
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
    assert bulk(TEACHER, BulkUpdateQuestions([a.id, b.id], status="approved", difficulty="vd", add_tag_ids=[TAG_A])).updated == 2
    assert a.status == b.status == "approved" and "OCR" not in a.issues and a.difficulty == "vd"
    assert set(qs.tags[b.id]) == {TAG_A, TAG_B}
    # a decision taken back is the same command (review-ux ADR-02): the question goes back on the desk
    assert bulk(TEACHER, BulkUpdateQuestions([a.id], status="needs_review")).updated == 1 and a.status == "needs_review"
    with pytest.raises(NotFound):
        bulk(TEACHER, BulkUpdateQuestions([a.id, uuid.uuid4()], difficulty="nb"))
    with pytest.raises(Invalid):
        bulk(TEACHER, BulkUpdateQuestions([a.id], status="flagged"))
    broken = parsed(qs, stem="", status="needs_review", issues=["thiếu đề bài"], number=7)
    with pytest.raises(Conflict) as e:
        bulk(TEACHER, BulkUpdateQuestions([broken.id], status="approved"))
    assert e.value.message.startswith("Câu 7 còn lỗi")


def test_every_human_path_marks_the_difficulty_as_a_persons_and_a_machine_never_overwrites_it(ports):
    """difficulty-at-upload AC-04: create, single edit and the bulk bar all leave `manual` behind, the level is
    checked on every one of them, and a machine pass leaves a level a person set exactly where it is (ADR-04)."""
    qs, tax, log, settings, views, uow = ports
    create = CreateQuestionHandler(qs, tax, log, views, uow)
    update = UpdateQuestionHandler(qs, tax, log, settings, views, uow)
    bulk = BulkUpdateQuestionsHandler(qs, tax, log, uow)
    made = qs.rows[create(TEACHER, CreateQuestion(stem="1 + 1 = ?", options=OPTS, answer={"key": "B"}, difficulty="vd")).id]
    assert (made.difficulty, made.difficulty_source) == ("vd", "manual")
    with pytest.raises(Invalid):
        create(TEACHER, CreateQuestion(stem="1 + 1 = ?", options=OPTS, answer={"key": "B"}, difficulty="kho"))

    q = parsed(qs, stem="a", answer={"key": "A"}, difficulty="nb", difficulty_source="auto")
    update(TEACHER, UpdateQuestion(q.id, difficulty="vdc", sent=frozenset({"difficulty"})))
    assert (q.difficulty, q.difficulty_source) == ("vdc", "manual")
    with pytest.raises(Invalid):  # the hole PATCH /questions/{id} left open: any string used to be stored as a level
        update(TEACHER, UpdateQuestion(q.id, difficulty="kho", sent=frozenset({"difficulty"})))
    update(TEACHER, UpdateQuestion(q.id, difficulty="", sent=frozenset({"difficulty"})))
    assert (q.difficulty, q.difficulty_source) == (None, None)  # no level, no provenance to claim

    bulk(TEACHER, BulkUpdateQuestions([q.id], difficulty="th"))
    assert (q.difficulty, q.difficulty_source) == ("th", "manual")
    assert not fill_difficulty(q, "vdc", "ai") and (q.difficulty, q.difficulty_source) == ("th", "manual")
    machine = parsed(qs, stem="b", answer={"key": "A"})
    assert fill_difficulty(machine, "nb", "auto") and (machine.difficulty, machine.difficulty_source) == ("nb", "auto")
    assert fill_difficulty(machine, "vd", "ai") and (machine.difficulty, machine.difficulty_source) == ("vd", "ai")
    with pytest.raises(Invalid):
        fill_difficulty(machine, "vd", "somewhere")
    # the trace is recorded so an undo can put it back, but it is not something a person changed: one edit, one field
    moved = [e for e in log.events if e[0] == q.id][-1]
    assert moved[2]["difficulty_source"] is None and moved[3]["difficulty_source"] == "manual"
    assert changed_fields(moved[2], moved[3]) == ["difficulty"]


def test_undo_puts_back_the_level_together_with_who_set_it(ports):
    """AC-04: the pipeline's `auto` level comes back as the pipeline's, not as a level the teacher chose."""
    qs, tax, log, _, _, uow = ports
    bulk, undo = BulkUpdateQuestionsHandler(qs, tax, log, uow), UndoBatchHandler(qs, tax, log, uow)
    a = parsed(qs, stem="a", answer={"key": "A"}, difficulty="nb", difficulty_source="auto")
    bulk(TEACHER, BulkUpdateQuestions([a.id], difficulty="vdc"))
    undo(TEACHER, UndoBatch(next(iter(log.batches(a.id)))))
    assert (a.difficulty, a.difficulty_source) == ("nb", "auto")
    # an event written before the trace existed names no source; a level in one can only have been a person's
    old = parsed(qs, stem="b", answer={"key": "A"}, difficulty="th", difficulty_source="ai")
    log.events.append((old.id, "bulk", {"difficulty": "nb"}, {"difficulty": "th"}, (batch := uuid.uuid4())))
    undo(TEACHER, UndoBatch(batch))
    assert (old.difficulty, old.difficulty_source) == ("nb", "manual")


def test_a_bulk_event_records_everything_the_bar_can_change_and_older_events_still_read(ports):
    """A-02: the recorded state is what an undo has to put back, so it holds every field the bulk bar sets — topics
    and tags included — and a placement or a tag change carries its own before, not only its after."""
    qs, tax, log, _, _, uow = ports
    bulk = BulkUpdateQuestionsHandler(qs, tax, log, uow)
    a = parsed(qs, stem="a", answer={"key": "A"}, status="needs_review", difficulty="nb", grade=10, subject_id=SUBJECT)
    qs.topics[a.id], qs.tags[a.id] = ([SUB_TOPIC], SUB_TOPIC), [TAG_B]
    assert bulk(TEACHER, BulkUpdateQuestions([a.id], difficulty="vdc", grade=11, primary_topic_id=TOPIC, add_tag_ids=[TAG_A])).updated == 1
    placed, tagged, moved = (e for e in log.events if e[0] == a.id)
    assert len(log.batches(a.id)) == 1  # one request, one batch: the placement, the tags and the edit are one unit
    assert placed[1:4] == ("topic", {"topics": [str(SUB_TOPIC)], "primary_topic": str(SUB_TOPIC)},
                           {"topics": [str(TOPIC)], "primary_topic": str(TOPIC)})
    assert tagged[1:4] == ("tag", {"tags": [str(TAG_B)]}, {"tags": sorted([str(TAG_A), str(TAG_B)])})
    before, after = moved[2], moved[3]
    assert changed_fields(before, after) == ["difficulty", "grade", "topics", "primary_topic", "tags"]
    assert (before["difficulty"], before["grade"], before["subject_id"]) == ("nb", 10, str(SUBJECT))
    assert before["topics"] == [str(SUB_TOPIC)] and before["primary_topic"] == str(SUB_TOPIC) and before["tags"] == [str(TAG_B)]
    assert (after["difficulty"], after["grade"], after["topics"]) == ("vdc", 11, [str(TOPIC)])
    # an event written before the snapshot widened: a field it does not mention is unknown, never "was empty"
    assert changed_fields({"status": "needs_review"}, {"status": "approved", "difficulty": "vd"}) == ["status"]
    assert changed_fields(None, None) == [] and changed_fields({"tags": []}, None) == []


def test_a_batch_is_named_by_its_coarsest_action_and_says_why_it_cannot_be_taken_back():
    """ADR-02: seven days, and the most specific refusal wins — a batch that was undone says so, not that it is old."""
    now = datetime(2026, 9, 23, 10, tzinfo=UTC)
    assert batch_action({"topic", "tag", "bulk"}) == "bulk" and batch_action({"topic", "tag"}) == "topic"
    assert batch_action({"undo", "bulk"}) == "undo" and batch_action(()) == ""
    assert undo_block(True, "bulk", now - timedelta(days=6, hours=23), now, False) is None
    assert undo_block(True, "bulk", now - timedelta(days=7, seconds=1), now, False) == "expired"
    assert undo_block(True, "bulk", now, now, True) == "already_undone"
    assert undo_block(True, "undo", now, now, False) == "is_undo"  # an undo is not undone a second time (A-04)
    assert undo_block(False, "bulk", now - timedelta(days=400), now, True) == "no_batch"  # written before batches existed
    assert set(BLOCKED) == {"no_batch", "is_undo", "already_undone", "expired"}


def test_recent_changes_are_read_within_the_callers_organisation():
    class FakeEvents:
        def __init__(self):
            self.asked: list = []

        def batches(self, org_id, req):
            self.asked.append((org_id, req))
            return Page([], 0, req.page, req.limit)

    events = FakeEvents()
    req = SearchRequest(page=2, limit=5)
    assert SearchQuestionEventsHandler(events)(TEACHER, SearchQuestionEvents(req)).total == 0
    assert events.asked == [(ORG, req)]


def test_a_bulk_edit_answers_with_the_batch_it_was_recorded_under(ports):
    """AC-01: the toast offers "Hoàn tác" for the edit it just reported, so the answer has to carry the batch —
    hunting for one's own edit in the history is a second request and a guess at which row is mine."""
    qs, tax, log, _, _, uow = ports
    bulk, undo = BulkUpdateQuestionsHandler(qs, tax, log, uow), UndoBatchHandler(qs, tax, log, uow)
    a = parsed(qs, stem="a", answer={"key": "A"}, difficulty="nb")
    r = bulk(TEACHER, BulkUpdateQuestions([a.id], difficulty="vdc"))
    assert (r.updated, r.batch_id) == (1, next(iter(log.batches(a.id))))
    assert undo(TEACHER, UndoBatch(r.batch_id)).restored == 1 and a.difficulty == "nb"


def test_undo_puts_a_whole_batch_back_through_the_aggregate(ports):
    """AC-01: every field the bar moved goes back — status, mức độ, lớp, môn, the placement and the tags — and the
    restore is itself an event, under a new batch naming the one it took back (A-04)."""
    qs, tax, log, _, _, uow = ports
    bulk, undo = BulkUpdateQuestionsHandler(qs, tax, log, uow), UndoBatchHandler(qs, tax, log, uow)
    a = parsed(qs, stem="a", answer={"key": "A"}, status="needs_review", difficulty="nb", grade=10, subject_id=SUBJECT)
    b = parsed(qs, stem="b", answer={"key": "B"}, status="needs_review", difficulty="th", grade=11, subject_id=SUBJECT)
    qs.topics[a.id], qs.tags[a.id] = ([SUB_TOPIC], SUB_TOPIC), [TAG_B]
    qs.topics[b.id], qs.tags[b.id] = ([TOPIC], TOPIC), []
    assert bulk(TEACHER, BulkUpdateQuestions([a.id, b.id], status="approved", difficulty="vdc", grade=12,
                                             primary_topic_id=TOPIC, add_tag_ids=[TAG_A])).updated == 2
    batch = next(iter(log.batches(a.id)))
    r = undo(TEACHER, UndoBatch(batch))
    assert (r.restored, r.batch_id != batch, uow.commits) == (2, True, 2)
    assert (a.status, a.difficulty, a.grade, a.subject_id) == ("needs_review", "nb", 10, SUBJECT)
    assert qs.topics[a.id] == ([SUB_TOPIC], SUB_TOPIC) and qs.tags[a.id] == [TAG_B]
    assert (b.status, b.difficulty, b.grade) == ("needs_review", "th", 11)
    assert qs.topics[b.id] == ([TOPIC], TOPIC) and qs.tags[b.id] == []
    written = [e for e in log.events if e[4] == r.batch_id]
    assert {e[1] for e in written} == {"undo", "topic", "tag"}  # the placement and the tags go back the way an edit sets them
    assert all(e[3][UNDONE_BATCH] == str(batch) for e in written if e[1] == "undo")
    assert written[-1][0] is None and written[-1][3]["questions"] == 2  # the batch says what it took back, whatever it restored


def test_a_batch_merges_its_partial_snapshots_earliest_value_first():
    """A-02: an event records only its own fields, so the state to restore is the union of the batch's `before`s;
    where two of them name the same field, the value to keep is the one the request found, not one it wrote."""
    q, other = uuid.uuid4(), uuid.uuid4()

    def ev(question_id, action, before, after):
        return ReviewEvent(organization_id=ORG, question_id=question_id, action=action, before=before, after=after)

    placed = ev(q, "topic", {"topics": [str(TOPIC)], "primary_topic": str(TOPIC)},
                {"topics": [str(SUB_TOPIC)], "primary_topic": str(SUB_TOPIC)})
    targets = restore_targets([placed,
                               ev(q, "tag", {"tags": [str(TAG_B)]}, {"tags": [str(TAG_A)]}),
                               ev(q, "bulk", {"status": "needs_review", "difficulty": "nb"}, {"status": "approved", "difficulty": "vdc"}),
                               ev(None, "bulk", None, {"pairs": 2, "updated": 2}),  # a batch's summary line is about no question
                               ev(other, "topic", {"topics": [], "primary_topic": None}, {"topics": [str(TOPIC)], "primary_topic": str(TOPIC)})])
    assert set(targets) == {q, other}
    assert targets[q] == {"status": "needs_review", "difficulty": "nb", "topics": [str(TOPIC)], "primary_topic": str(TOPIC),
                          "tags": [str(TAG_B)]}
    assert targets[other] == {"topics": [], "primary_topic": None}  # "was nowhere" is a state to restore, not a missing key
    # one question placed twice in the same request: the second event's before is what the first wrote, and the events
    # of one request share a timestamp — so the answer is the value no event produced, whichever order they arrive in
    twice = [placed, ev(q, "topic", {"topics": [str(SUB_TOPIC)], "primary_topic": str(SUB_TOPIC)},
                        {"topics": [str(OTHER_TOPIC)], "primary_topic": str(OTHER_TOPIC)})]
    assert restore_targets(twice)[q]["primary_topic"] == str(TOPIC)
    assert restore_targets(list(reversed(twice)))[q]["primary_topic"] == str(TOPIC)


def test_undo_refuses_the_whole_batch_when_a_question_is_gone(ports):
    """AC-02: a question that no longer exists stops the lot, and the refusal names it."""
    qs, tax, log, _, _, uow = ports
    bulk, undo = BulkUpdateQuestionsHandler(qs, tax, log, uow), UndoBatchHandler(qs, tax, log, uow)
    a = parsed(qs, stem="a", answer={"key": "A"}, difficulty="nb")
    b = parsed(qs, stem="b", answer={"key": "B"}, difficulty="nb")
    assert bulk(TEACHER, BulkUpdateQuestions([a.id, b.id], difficulty="vdc")).updated == 2
    batch = next(iter(log.batches(a.id)))
    qs.remove(b)
    with pytest.raises(Invalid) as e:
        undo(TEACHER, UndoBatch(batch))
    assert e.value.code == "questions_gone" and e.value.fields["question_ids"] == [str(b.id)]
    assert a.difficulty == "vdc" and uow.commits == 1  # the one that is still there was not restored either
    with pytest.raises(NotFound) as e:
        undo(TEACHER, UndoBatch(uuid.uuid4()))
    assert e.value.code == "batch_not_found"
    # a row from before migration 0020, when deleting a question emptied the question of the events it had left
    # behind: the batch is refused all the same, and that row has no id to give because none was kept
    orphaned = uuid.uuid4()
    log.record(ORG, TEACHER.user_id, None, "bulk", {"difficulty": "nb"}, {"difficulty": "vdc"}, orphaned)
    log.record(ORG, TEACHER.user_id, a.id, "bulk", {"difficulty": "nb"}, {"difficulty": "vdc"}, orphaned)
    with pytest.raises(Invalid) as e:
        undo(TEACHER, UndoBatch(orphaned))
    assert e.value.code == "questions_gone" and e.value.fields["question_ids"] == [] and "đã bị xóa" in e.value.message
    # since 0020 a deleted question keeps its id in the history, so the same refusal can name it (AC-03)
    named = uuid.uuid4()
    log.record(ORG, TEACHER.user_id, uuid.uuid4(), "bulk", {"difficulty": "nb"}, {"difficulty": "vdc"}, named)
    with pytest.raises(Invalid) as e:
        undo(TEACHER, UndoBatch(named))
    assert e.value.code == "questions_gone" and len(e.value.fields["question_ids"]) == 1
    # a batch's own summary line is about no question and is not one of those: it says a count and a document
    assert not lost_question(ReviewEvent(organization_id=ORG, action="bulk", before={"status": "auto_approved"},
                                         after={"status": "approved", "count": 3, "document": str(DOC)}))


def test_undo_runs_the_guards_an_edit_runs(ports):
    """ADR-04: the restore goes through the same checks, so it can refuse — a subject that would leave the question
    in another subject's tree, or a grade the organisation no longer teaches."""
    qs, tax, log, _, _, uow = ports
    undo = UndoBatchHandler(qs, tax, log, uow)
    a = parsed(qs, stem="a", answer={"key": "A"}, subject_id=OTHER_SUBJECT, grade=11)
    qs.topics[a.id] = ([OTHER_TOPIC], OTHER_TOPIC)
    subject_batch, grade_batch = uuid.uuid4(), uuid.uuid4()
    log.record(ORG, TEACHER.user_id, a.id, "bulk", {"subject_id": str(SUBJECT)}, {"subject_id": str(OTHER_SUBJECT)}, subject_batch)
    log.record(ORG, TEACHER.user_id, a.id, "bulk", {"grade": 9}, {"grade": 11}, grade_batch)
    with pytest.raises(Invalid) as e:
        undo(TEACHER, UndoBatch(subject_batch))
    assert e.value.code == "subject_topic_conflict" and "Dao động" in e.value.message
    with pytest.raises(Invalid) as e:
        undo(TEACHER, UndoBatch(grade_batch))
    assert e.value.fields == {"grade": "Lớp không hợp lệ"}
    assert (a.subject_id, a.grade, uow.commits) == (OTHER_SUBJECT, 11, 0)


def test_a_batch_is_taken_back_once_and_not_after_the_window(ports):
    """AC-04 / AC-05: a second undo is refused and names the one that already ran, an undo is not itself undone, and
    a batch past the window is refused with its age."""
    qs, tax, log, _, _, uow = ports
    bulk, undo = BulkUpdateQuestionsHandler(qs, tax, log, uow), UndoBatchHandler(qs, tax, log, uow)
    a = parsed(qs, stem="a", answer={"key": "A"}, difficulty="nb")
    assert bulk(TEACHER, BulkUpdateQuestions([a.id], difficulty="vdc")).updated == 1
    batch = next(iter(log.batches(a.id)))
    first = undo(TEACHER, UndoBatch(batch))
    assert a.difficulty == "nb"
    # the batch moved neither the placement nor the tags, so the restore leaves the links alone — rewriting them
    # would turn a classifier's suggestion into a teacher's own placement; its only events are the undo itself
    assert {e[1] for e in log.events if e[4] == first.batch_id} == {"undo"}
    with pytest.raises(Conflict) as e:
        undo(TEACHER, UndoBatch(batch))
    assert e.value.code == "batch_already_undone" and e.value.fields == {"undone_by": str(first.batch_id)}
    with pytest.raises(Conflict) as e:
        undo(TEACHER, UndoBatch(first.batch_id))
    assert e.value.code == "batch_is_undo"
    log.at = datetime.now(UTC) - UNDO_WINDOW - timedelta(days=1)
    old = uuid.uuid4()
    log.record(ORG, TEACHER.user_id, a.id, "bulk", {"difficulty": "th"}, {"difficulty": "nb"}, old)
    with pytest.raises(Invalid) as e:
        undo(TEACHER, UndoBatch(old))
    assert e.value.code == "batch_expired" and e.value.fields["age_days"] == UNDO_WINDOW.days + 1
    assert a.difficulty == "nb"


def test_bulk_sets_subject_and_grade_and_refuses_a_topic_of_another_subject(ports):
    qs, tax, log, _, _, uow = ports
    bulk = BulkUpdateQuestionsHandler(qs, tax, log, uow)
    a = parsed(qs, stem="a", answer={"key": "A"}, status="needs_review")
    b = parsed(qs, stem="b", answer={"key": "B"}, status="needs_review")
    assert bulk(TEACHER, BulkUpdateQuestions([a.id, b.id], subject_id=SUBJECT, grade=11)).updated == 2
    assert a.subject_id == b.subject_id == SUBJECT and a.grade == b.grade == 11
    with pytest.raises(Invalid) as e:
        bulk(TEACHER, BulkUpdateQuestions([a.id], grade=9))
    assert e.value.fields == {"grade": "Lớp không hợp lệ"}
    with pytest.raises(Invalid) as e:
        bulk(TEACHER, BulkUpdateQuestions([a.id], subject_id=uuid.uuid4()))
    assert e.value.fields == {"subject_id": "Môn học không hợp lệ"}
    # a question already placed in another subject's tree: nothing is applied and the conflict is named (A-04)
    qs.topics[b.id] = ([OTHER_TOPIC], OTHER_TOPIC)
    with pytest.raises(Invalid) as e:
        bulk(TEACHER, BulkUpdateQuestions([a.id, b.id], subject_id=SUBJECT, grade=12))
    assert e.value.code == "subject_topic_conflict" and "Dao động" in e.value.message
    assert e.value.fields["conflicts"] == [{"question_id": str(b.id), "topic_id": str(OTHER_TOPIC), "topic_name": "Dao động"}]
    assert a.grade == 11  # refused before anything was touched
    assert bulk(TEACHER, BulkUpdateQuestions([b.id], subject_id=OTHER_SUBJECT)).updated == 1 and b.subject_id == OTHER_SUBJECT
    # the topic set in the same request is what the new subject is checked against
    assert bulk(TEACHER, BulkUpdateQuestions([b.id], subject_id=SUBJECT, primary_topic_id=TOPIC)).updated == 1
    assert qs.topics[b.id] == ([TOPIC], TOPIC) and b.subject_id == SUBJECT


def test_bulk_topics_applies_each_pair_and_names_what_it_skipped(ports):
    qs, tax, log, _, _, uow = ports
    bulk = BulkSetTopicsHandler(qs, tax, log, uow)
    a = parsed(qs, stem="a", subject_id=SUBJECT)
    b = parsed(qs, stem="b", subject_id=SUBJECT)
    homeless = parsed(qs, stem="c")                                   # no subject yet: nothing to check the topic against
    foreign = Question(organization_id=uuid.uuid4(), stem="d", subject_id=SUBJECT, options=list(OPTS))
    qs.add(foreign)
    gone, unknown_topic = uuid.uuid4(), uuid.uuid4()
    r = bulk(TEACHER, BulkSetTopics([(a.id, TOPIC), (b.id, SUB_TOPIC), (a.id, OTHER_TOPIC), (homeless.id, TOPIC),
                                     (foreign.id, TOPIC), (gone, TOPIC), (b.id, unknown_topic)]))
    assert r.updated == 2 and uow.commits == 1
    assert qs.topics[a.id] == ([TOPIC], TOPIC) and qs.topics[b.id] == ([SUB_TOPIC], SUB_TOPIC)
    assert [(s.question_id, s.reason) for s in r.skipped] == [
        (a.id, "subject_mismatch"), (homeless.id, "no_subject"), (foreign.id, "other_org"),
        (gone, "unknown_question"), (b.id, "unknown_topic")]
    assert r.skipped[0].message == "Chuyên đề không thuộc môn của câu hỏi"
    assert log.actions(a.id) == ["topic"] and log.actions()[-1] == "bulk"  # the whole call is audited once, with its size
    assert log.events[-1][3] == {"pairs": 7, "updated": 2, "skipped": 5}
    with pytest.raises(Invalid) as e:
        bulk(TEACHER, BulkSetTopics([(a.id, TOPIC)] * 201))
    assert e.value.fields == {"pairs": "Tối đa 200 cặp câu hỏi – chuyên đề mỗi lần"}


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


def test_document_questions_by_state(ports):
    qs, _, _, _, views, _ = ports
    parsed(qs, stem="a", status="needs_review", issues=["thiếu đáp án"], number=1)
    parsed(qs, stem="b", answer={"key": "A"}, status="auto_approved", spot_check=True, number=2)
    parsed(qs, stem="c", answer={"key": "A"}, status="auto_approved", number=3)
    parsed(qs, stem="d", answer={"key": "A"}, status="approved", number=4)
    parsed(qs, stem="e", status="rejected", number=5)
    handle = SearchDocumentQuestionsHandler(FakeDocuments(), FakeReviewReader(qs), views)

    def numbers(state="pending", **kw):
        return [v.number for v in handle(TEACHER, SearchDocumentQuestions(DOC, SearchRequest(**kw), state)).data]

    # what still waits is the default, and it says why; the check sample that nobody looked at belongs to it
    page = handle(TEACHER, SearchDocumentQuestions(DOC, SearchRequest()))
    assert [v.number for v in page.data] == [1, 2] and page.total == 2
    assert [v.group for v in page.data] == ["thiếu đáp án", "Kiểm tra ngẫu nhiên"]
    assert numbers("approved") == [3, 4] and numbers("rejected") == [5] and numbers("duplicate") == []
    assert numbers("all") == [1, 2, 3, 4, 5] and numbers("all", page=2, limit=2) == [3, 4]
    assert all(v.group is None for v in handle(TEACHER, SearchDocumentQuestions(DOC, SearchRequest(), "approved")).data)
    with pytest.raises(Invalid) as e:
        handle(TEACHER, SearchDocumentQuestions(DOC, SearchRequest(), "nope"))
    assert e.value.code == "bad_filter"
    with pytest.raises(NotFound):
        handle(TEACHER, SearchDocumentQuestions(uuid.uuid4(), SearchRequest()))


def test_review_state_is_derived_from_the_counts():
    zero = dict.fromkeys(STATUS_KEYS, 0)
    assert review_state(0, zero, 0) == "done"  # a document without questions has nothing left to do
    assert review_state(3, {**zero, "needs_review": 1, "approved": 2}, 0) == "pending"
    assert review_state(3, {**zero, "flagged": 1, "approved": 2}, 0) == "pending"
    # the part of the check sample nobody looked at still waits, even though the machine approved it
    sampled = {**zero, "auto_approved": 3}
    assert pending_count(sampled, 1) == 1 and review_state(3, sampled, 1) == "pending"
    assert pending_count(sampled, 0) == 0 and review_state(3, sampled, 0) == "done"
    assert review_state(3, {**zero, "approved": 1, "rejected": 1, "duplicate": 1}, 0) == "done"
    assert review_state(3, {**zero, "approved": 2}, 0) == "in_progress"  # one question nobody triaged yet


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


# -------------------------------------------------------------- the tagging queue (topic-coverage ADR-01, ADR-02)


class FakeSuggestions:
    """The ingestion classifier: whatever it was told to answer, plus what it was asked."""

    def __init__(self, answers=None, model_used=False):
        self.answers = answers or {}
        self.model_used = model_used
        self.asked: list = []

    def suggest_for(self, org_id, subject_id, items, use_model=True):
        self.asked.append((org_id, subject_id, [i for i, _ in items], use_model))
        return {qid: self.answers.get(qid, []) for qid, _ in items}, self.model_used and use_model


def test_suggestions_carry_the_topic_name_path_score_and_source(ports):
    qs, taxonomy = ports[0], ports[1]
    q = parsed(qs, type="mcq", stem="Tính nguyên hàm", subject_id=SUBJECT, status="auto_approved")
    ports_ = FakeSuggestions({q.id: [(TOPIC, 0.8, "keyword"), (SUB_TOPIC, 0.4, "ai")]}, model_used=True)
    found = SuggestTopicsHandler(qs, taxonomy, ports_)(TEACHER, SuggestTopics([q.id]))
    assert [(s.topic_id, s.name, s.path, s.score, s.source) for s in found.by_question[q.id]] == [
        (TOPIC, "Nguyên hàm", "t1", 0.8, "keyword"), (SUB_TOPIC, "Tích phân", "t1.t2", 0.4, "ai")]
    # the classifier is asked per subject, with the stem and the options, and says whether the model answered
    assert ports_.asked == [(ORG, SUBJECT, [q.id], True)] and found.model_used


def test_the_queue_can_ask_for_the_rules_alone(ports):
    """AC-07 seen from the bank: no model call, and the answer says the model was not used."""
    qs, taxonomy = ports[0], ports[1]
    q = parsed(qs, type="mcq", stem="Tính nguyên hàm", subject_id=SUBJECT)
    suggestions = FakeSuggestions({q.id: [(TOPIC, 0.8, "keyword")]}, model_used=True)
    found = SuggestTopicsHandler(qs, taxonomy, suggestions)(TEACHER, SuggestTopics([q.id], use_model=False))
    assert not found.model_used and suggestions.asked == [(ORG, SUBJECT, [q.id], False)]
    assert [s.source for s in found.by_question[q.id]] == ["keyword"]


def test_questions_are_grouped_by_subject_and_a_topic_of_another_org_is_dropped(ports):
    qs, taxonomy = ports[0], ports[1]
    a = parsed(qs, type="mcq", stem="Câu Toán", subject_id=SUBJECT)
    b = parsed(qs, type="mcq", stem="Câu không môn", subject_id=None)
    suggestions = FakeSuggestions({a.id: [(TOPIC, 0.7, "keyword")], b.id: [(uuid.uuid4(), 0.9, "ai")]})
    found = SuggestTopicsHandler(qs, taxonomy, suggestions)(TEACHER, SuggestTopics([a.id, b.id]))
    assert {s for _, s, _, _ in suggestions.asked} == {None, SUBJECT}  # one call per subject
    assert [s.name for s in found.by_question[a.id]] == ["Nguyên hàm"] and found.by_question[b.id] == []
    assert not found.model_used


def test_more_than_fifty_questions_is_a_validation_error(ports):
    qs, taxonomy = ports[0], ports[1]
    with pytest.raises(Invalid):
        SuggestTopicsHandler(qs, taxonomy, FakeSuggestions())(TEACHER, SuggestTopics([uuid.uuid4() for _ in range(MAX_QUESTIONS + 1)]))


def test_a_question_of_another_organisation_is_not_found(ports):
    qs, taxonomy = ports[0], ports[1]
    q = Question(organization_id=uuid.uuid4(), type="mcq", stem="Câu của trung tâm khác", options=list(OPTS))
    qs.add(q)
    suggestions = FakeSuggestions()
    with pytest.raises(NotFound):
        SuggestTopicsHandler(qs, taxonomy, suggestions)(TEACHER, SuggestTopics([q.id]))
    assert suggestions.asked == []


def test_an_unplaced_question_waits_for_review_whatever_its_confidence(ports):
    qs, uow = ports[0], ports[5]
    auto = parsed(qs, type="mcq", stem="Câu rõ ràng", status="auto_approved", confidence=0.99, spot_check=True)
    duplicate = parsed(qs, type="mcq", stem="Câu trùng", status="duplicate", confidence=0.99)
    already = parsed(qs, type="mcq", stem="Câu chờ duyệt", status="needs_review", confidence=0.2)
    moved = ReviewUntaggedHandler(qs, uow)(ReviewUntagged([auto.id, duplicate.id, already.id]))
    assert moved == 1
    assert auto.status == "needs_review" and duplicate.status == "duplicate" and already.status == "needs_review"
    assert auto.spot_check is False  # it is no longer a sample of what auto-approval let through
