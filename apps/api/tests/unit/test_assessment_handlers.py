"""Assessment handlers and rules against in-memory ports: scoring, the exam builder, assignments, attempts (ADR-02)."""
from datetime import UTC, datetime, timedelta
import random
import uuid

import pytest

from app.modules.assessment.application.commands.add_exam_questions import AddExamQuestions, AddExamQuestionsHandler
from app.modules.assessment.application.commands.apply_blueprint import ApplyBlueprint, ApplyBlueprintHandler
from app.modules.assessment.application.commands.create_assignment import CreateAssignment, CreateAssignmentHandler
from app.modules.assessment.application.commands.create_exam_from_document import CreateExamFromDocument, CreateExamFromDocumentHandler
from app.modules.assessment.application.commands.grade_essay import GradeEssay, GradeEssayHandler
from app.modules.assessment.application.commands.reorder_exam_questions import ReorderExamQuestions, ReorderExamQuestionsHandler
from app.modules.assessment.application.commands.save_answer import SaveAnswer, SaveAnswerHandler
from app.modules.assessment.application.commands.start_attempt import StartAttempt, StartAttemptHandler
from app.modules.assessment.application.commands.submit_attempt import SubmitAttempt, SubmitAttemptHandler
from app.modules.assessment.application.commands.sweep_expired_attempts import SweepExpiredAttemptsHandler
from app.modules.assessment.application.commands.update_exam import UpdateExam, UpdateExamHandler
from app.modules.assessment.application.common import Grading
from app.modules.assessment.application.queries.assignment_paper import AssignmentPaper, AssignmentPaperHandler
from app.modules.assessment.application.queries.attempt_result import AttemptResult, AttemptResultHandler
from app.modules.assessment.application.queries.my_assignments import MyAssignmentsHandler
from app.modules.assessment.application.queries.trial_run import TrialRun, TrialRunHandler
from app.modules.assessment.domain.entities import Assignment, Attempt, AttemptAnswer, Exam, ExamQuestion
from app.modules.assessment.domain.services import assignment_rules, attempt_rules, scoring
from app.modules.assessment.domain.value_objects import DocumentRef, QuestionRef, Snapshot
from app.shared.application.actor import Actor
from app.shared.domain.errors import Conflict, Forbidden, Invalid, NotFound
from tests.unit.fakes import FakeUow

ORG = uuid.uuid4()
TEACHER = Actor(user_id=uuid.uuid4(), org_id=ORG, role="teacher")
STUDENT = Actor(user_id=uuid.uuid4(), org_id=ORG, role="student")
OTHER = Actor(user_id=uuid.uuid4(), org_id=ORG, role="student")
CLASS = uuid.uuid4()
TOPIC_A, TOPIC_B, YEAR = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
NOW = datetime(2026, 9, 22, 8, 0, tzinfo=UTC)
OPTS = [{"label": lab, "content": c} for lab, c in zip("ABCD", ("1", "2", "3", "4"))]
TF_OPTS = [{"label": lab, "content": c, "is_true": v} for lab, c, v in zip("abcd", "wxyz", (True, False, True, True))]


class Clock:
    def __init__(self, at: datetime = NOW):
        self.at = at

    def __call__(self) -> datetime:
        return self.at


def mcq(key="B", status="approved", topic=TOPIC_A, **kw) -> QuestionRef:
    return QuestionRef(id=uuid.uuid4(), organization_id=ORG, type="mcq", status=status, stem="Câu", options=OPTS, answer={"key": key}, **kw)


def tf() -> QuestionRef:
    return QuestionRef(id=uuid.uuid4(), organization_id=ORG, type="true_false", status="approved", options=TF_OPTS,
                       answer={"a": True, "b": False, "c": True, "d": True})


def essay() -> QuestionRef:
    return QuestionRef(id=uuid.uuid4(), organization_id=ORG, type="essay", status="approved", answer={"text": "Mẫu"})


class FakeExams:
    def __init__(self):
        self.rows: dict = {}
        self.eqs: list[ExamQuestion] = []
        self.taken: set = set()

    def get(self, org_id, exam_id):
        e = self.rows.get(exam_id)
        return e if e is not None and e.organization_id == org_id else None

    def get_any(self, exam_id):
        return self.rows.get(exam_id)

    def subjects_of(self, exam_ids):
        return {i: getattr(self.rows.get(i), "subject_id", None) for i in exam_ids}

    def add(self, exam):
        self.rows[exam.id] = exam

    def remove(self, exam):
        del self.rows[exam.id]

    def questions(self, exam_id):
        return sorted((eq for eq in self.eqs if eq.exam_id == exam_id), key=lambda eq: eq.position)

    def question(self, exam_id, question_id):
        return next((eq for eq in self.eqs if eq.exam_id == exam_id and eq.question_id == question_id), None)

    def add_question(self, eq):
        self.eqs.append(eq)

    def remove_question(self, eq):
        self.eqs.remove(eq)

    def clear(self, exam_id):
        self.eqs = [eq for eq in self.eqs if eq.exam_id != exam_id]

    def has_attempts(self, exam_id):
        return exam_id in self.taken

    def uses_question(self, question_id):
        return any(eq.question_id == question_id for eq in self.eqs)


class FakeBank:
    def __init__(self, *refs: QuestionRef, topics: dict | None = None):
        self.refs = {q.id: q for q in refs}
        self.topics = topics or {}  # question id → topic id

    def add(self, *refs):
        for q in refs:
            self.refs[q.id] = q

    def questions(self, org_id, ids):
        return [self.refs[i] for i in ids if i in self.refs and (org_id is None or self.refs[i].organization_id == org_id)]

    def of_document(self, document_id):
        return [q for q in self.refs.values() if q.source_document_id == document_id]

    def pool(self, org_id, f):
        return sorted(q.id for q in self.refs.values() if q.usable and (f.type is None or q.type == f.type)
                      and (f.topic_id is None or self.topics.get(q.id) == f.topic_id))

    def views(self, org_id, ids):
        return {i: {"id": i, "type": self.refs[i].type, "topics": [{"name": "Đại số", "is_primary": True}] if i in self.topics else []}
                for i in ids if i in self.refs}

    def classification(self, ids):
        return {i: ("dai_so" if i in self.topics else None, []) for i in ids}


class FakeAssignments:
    def __init__(self):
        self.rows: dict = {}
        self.target_rows: list = []

    def get(self, org_id, assignment_id):
        a = self.rows.get(assignment_id)
        return a if a is not None and a.organization_id == org_id else None

    def get_any(self, assignment_id):
        return self.rows.get(assignment_id)

    def add(self, a, targets):
        self.rows[a.id] = a
        self.target_rows += targets

    def remove(self, a):
        del self.rows[a.id]

    def targets(self, assignment_id):
        return [t for t in self.target_rows if t.assignment_id == assignment_id]

    def for_student(self, org_id, user_id, class_ids):
        return [a for a in self.rows.values() if any(t.user_id == user_id or t.class_id in class_ids for t in self.targets(a.id))]


class FakeAttempts:
    def __init__(self, clock: "Clock | None" = None):
        self.rows: dict = {}
        self.answer_rows: dict = {}
        self.clock = clock or Clock()

    def get(self, org_id, attempt_id):
        att = self.rows.get(attempt_id)
        return att if att is not None and att.organization_id == org_id else None

    def add(self, att):
        att.started_at = att.started_at or self.clock()
        self.rows[att.id] = att

    def of_student(self, assignment_id, student_id):
        return [t for t in self.rows.values() if t.assignment_id == assignment_id and t.student_id == student_id]

    def current(self, assignment_id, student_id):
        return next((t for t in self.of_student(assignment_id, student_id) if t.status == "in_progress"), None)

    def count(self, assignment_id, student_id=None):
        return len([t for t in self.rows.values() if t.assignment_id == assignment_id and (student_id is None or t.student_id == student_id)])

    def expired(self, before):
        return [t for t in self.rows.values() if t.status == "in_progress" and t.deadline_at < before]

    def answer(self, attempt_id, question_id):
        return self.answer_rows.get((attempt_id, question_id))

    def answers(self, attempt_id):
        return [a for (att, _), a in self.answer_rows.items() if att == attempt_id]

    def add_answer(self, ans):
        self.answer_rows[(ans.attempt_id, ans.question_id)] = ans

    def count_tab_switch(self, att):
        att.tab_switches += 1
        return att.tab_switches

    def flush(self):
        pass


class FakeFacts:
    def __init__(self, attempts: "FakeAttempts"):
        self.rows: dict = {}
        self.attempts = attempts

    def replace(self, attempt_id, question_id, fact):
        self.rows.pop((attempt_id, question_id), None)
        if fact is not None:
            self.rows[(attempt_id, question_id)] = fact

    def earlier(self, student_id, question_id, attempt_id, before):
        return any(f.student_id == student_id and f.question_id == question_id and f.attempt_id != attempt_id
                   and self.attempts.rows[f.attempt_id].started_at < before for f in self.rows.values())


class FakeListener:
    def __init__(self):
        self.facts: list = []

    def recorded(self, fact):
        self.facts.append(fact)


class FakeRoster:
    def __init__(self, members: dict | None = None, students: set | None = None):
        self.members = members or {}  # class id → user ids
        self.student_ids = students or set()

    def class_names(self, org_id, class_ids):
        return {c: f"Lớp {i}" for i, c in enumerate(class_ids) if c in self.members}

    def class_members(self, org_id, class_ids):
        return set().union(*(self.members.get(c, set()) for c in class_ids))

    def classes_of(self, org_id, user_id):
        return [c for c, m in self.members.items() if user_id in m]

    def students(self, org_id, user_ids, active_accounts=False):
        return set(user_ids) & self.student_ids

    def snapshot(self, org_id, student_id, when):
        return Snapshot(YEAR, "hk1", tuple(self.classes_of(org_id, student_id)))


class FakeSubjects:
    NAMES = {TOPIC_A: "Đại số", TOPIC_B: "Hình học"}

    def exists(self, org_id, subject_id):
        return False

    def topic_names(self, org_id, topic_ids):
        return {t: self.NAMES[t] for t in topic_ids if t in self.NAMES}


class World:
    """One org: an exam, its questions in the bank, a class with a student, the ports wired to handlers."""

    def __init__(self, *refs: QuestionRef, now: datetime = NOW):
        self.clock = Clock(now)
        self.exams, self.bank, self.assignments, self.attempts = FakeExams(), FakeBank(*refs), FakeAssignments(), FakeAttempts(self.clock)
        self.subjects = FakeSubjects()
        self.facts, self.listener = FakeFacts(self.attempts), FakeListener()
        self.roster = FakeRoster({CLASS: {STUDENT.user_id}}, {STUDENT.user_id, OTHER.user_id})
        self.uow = FakeUow()
        self.exam = Exam(organization_id=ORG, title="Kiểm tra")
        self.exams.add(self.exam)
        for i, q in enumerate(refs, start=1):
            self.exams.add_question(ExamQuestion(exam_id=self.exam.id, question_id=q.id, position=i, section=attempt_section(q.type),
                                                 points=self.exam.points_for(q.type)))

    def grading(self) -> Grading:
        return Grading(self.attempts, self.exams, self.bank, self.roster, self.facts, self.listener, self.clock)

    def assignment(self, **kw) -> Assignment:
        a = Assignment(organization_id=ORG, exam_id=self.exam.id, title="Bài 1", open_at=kw.pop("open_at", NOW - timedelta(hours=1)),
                       close_at=kw.pop("close_at", NOW + timedelta(hours=2)), duration_minutes=kw.pop("duration_minutes", 45), **kw)
        from app.modules.assessment.domain.entities import AssignmentTarget

        self.assignments.add(a, [AssignmentTarget(assignment_id=a.id, class_id=CLASS)])
        return a

    def start(self, a: Assignment, actor: Actor = STUDENT, rng=None) -> uuid.UUID:
        return StartAttemptHandler(self.assignments, self.attempts, self.exams, self.bank, self.roster, self.grading(), self.clock,
                                   self.uow, rng)(actor, StartAttempt(a.id))

    def save(self, att_id, qid, response, actor: Actor = STUDENT, seconds=None, first_seen=None):
        return SaveAnswerHandler(self.attempts, self.bank, self.grading(), self.clock, self.uow)(
            actor, SaveAnswer(att_id, qid, response, seconds, first_seen))

    def submit(self, att_id, actor: Actor = STUDENT):
        return SubmitAttemptHandler(self.attempts, self.grading(), self.clock, self.uow)(actor, SubmitAttempt(att_id))


def attempt_section(qtype: str) -> str:
    from app.modules.assessment.domain.services.exam_rules import section_of

    return section_of(qtype)


def shown_key(w: World, att_id, q: QuestionRef) -> str:
    """The label under which the student sees the correct MCQ option."""
    return attempt_rules.label_maps(w.attempts.rows[att_id], q)[1][q.answer["key"]]


# ------------------------------------------------------------------ scoring (THPT 2025)


@pytest.mark.parametrize("right,share", [(0, 0.0), (1, 0.1), (2, 0.25), (3, 0.5), (4, 1.0)])
def test_true_false_partial_credit_on_the_thpt_scale(right, share):
    key = {"a": True, "b": False, "c": True, "d": True}
    response = {k: (v if i < right else not v) for i, (k, v) in enumerate(key.items())}
    g = scoring.grade("true_false", key, response, 1.0)
    assert g.points == pytest.approx(share) and g.is_correct is (right == 4) and g.ratio == share


def test_scoring_edge_cases():
    assert scoring.grade("essay", {"text": "x"}, {"text": "y"}, 2.0).points is None
    assert scoring.grade("mcq", None, {"key": "A"}, 0.25) == scoring.Grade(0.0, 0.25, False, 0.0)
    assert scoring.grade("true_false", {"a": True, "b": False}, {"a": True}, 1.0).points == pytest.approx(0.5)  # not 4 statements
    assert scoring.grade("short_answer", {"value": "2,5"}, {"value": "5/2"}, 0.5).points == 0.5
    assert scoring.scaled(7.25, 10) == 7.25 and scoring.scaled(3, 4) == 7.5 and scoring.scaled(1, 0) == 0.0


# ------------------------------------------------------------------ exam builder


def test_blueprint_is_repeatable_with_a_seed_and_reports_shortfalls():
    qs = [mcq() for _ in range(6)] + [tf() for _ in range(2)]
    topics = {q.id: TOPIC_A for q in qs[:6]} | {q.id: TOPIC_B for q in qs[6:]}

    def draw():
        w = World()
        w.bank = FakeBank(*qs, topics=topics)
        r = ApplyBlueprintHandler(w.exams, w.bank, w.subjects, w.uow)(TEACHER, ApplyBlueprint(w.exam.id, [
            {"topic_id": str(TOPIC_B), "type": "true_false", "count": 3}, {"topic_id": str(TOPIC_A), "type": "mcq", "count": 4}], seed=7))
        return w, r

    w, r = draw()
    assert r == {"added": 6, "shortfalls": [{"row": 0, "missing": 1}]}
    rows = w.exams.questions(w.exam.id)
    assert [eq.section for eq in rows] == ["I"] * 4 + ["II"] * 2 and [eq.position for eq in rows] == list(range(1, 7))
    assert [eq.row for eq in rows] == [1] * 4 + [0] * 2 and sum(eq.points for eq in rows) == 3.0
    assert w.exam.source == "blueprint" and w.uow.commits == 1
    again, _ = draw()
    assert [eq.question_id for eq in again.exams.questions(again.exam.id)] == [eq.question_id for eq in rows]
    with pytest.raises(Invalid):
        ApplyBlueprintHandler(w.exams, w.bank, w.subjects, w.uow)(TEACHER, ApplyBlueprint(w.exam.id, [{"type": "mcq", "count": 2}]))
    with pytest.raises(Invalid) as bad:
        ApplyBlueprintHandler(w.exams, w.bank, w.subjects, w.uow)(TEACHER, ApplyBlueprint(w.exam.id, [{"topic_id": "x", "count": 2}]))
    assert bad.value.fields == {"topic_ids": "Chuyên đề không hợp lệ"}


def test_blueprint_refuses_a_row_whose_topic_holds_nothing():
    """A-05: a row on an empty topic is named and refused; a row that can be filled is untouched (AC-06)."""
    qs = [mcq() for _ in range(2)]
    w = World()
    w.bank = FakeBank(*qs, topics={q.id: TOPIC_A for q in qs})
    handle = ApplyBlueprintHandler(w.exams, w.bank, w.subjects, w.uow)
    with pytest.raises(Invalid) as e:
        handle(TEACHER, ApplyBlueprint(w.exam.id, [{"topic_id": str(TOPIC_A), "count": 1}, {"topic_id": str(TOPIC_B), "count": 2}]))
    assert e.value.code == "empty_topic" and "Hình học" in e.value.message
    assert e.value.fields["row"] == 1 and e.value.fields["topic_id"] == str(TOPIC_B) and e.value.fields["question_count"] == 0
    assert w.exams.questions(w.exam.id) == [] and w.uow.commits == 0  # nothing was touched
    # the topic holds questions but not of that type: still a shortfall, as before
    r = handle(TEACHER, ApplyBlueprint(w.exam.id, [{"topic_id": str(TOPIC_A), "type": "true_false", "count": 2}]))
    assert r == {"added": 0, "shortfalls": [{"row": 0, "missing": 2}]}


def test_an_exam_somebody_took_is_frozen_and_order_must_match():
    q1, q2 = mcq(), mcq()
    w = World(q1, q2)
    with pytest.raises(Invalid):
        ReorderExamQuestionsHandler(w.exams, w.uow)(TEACHER, ReorderExamQuestions(w.exam.id, [q1.id]))
    ReorderExamQuestionsHandler(w.exams, w.uow)(TEACHER, ReorderExamQuestions(w.exam.id, [q2.id, q1.id]))
    assert [eq.question_id for eq in w.exams.questions(w.exam.id)] == [q2.id, q1.id]
    w.exams.taken.add(w.exam.id)
    with pytest.raises(Conflict) as frozen:
        AddExamQuestionsHandler(w.exams, w.bank, w.uow)(TEACHER, AddExamQuestions(w.exam.id, [q1.id]))
    assert frozen.value.code == "exam_in_use"


def test_only_approved_questions_are_added_and_points_follow_the_type():
    q1, draft, t = mcq(), mcq(status="needs_review"), tf()
    w = World(q1)
    w.bank.add(draft, t)
    with pytest.raises(Invalid):
        AddExamQuestionsHandler(w.exams, w.bank, w.uow)(TEACHER, AddExamQuestions(w.exam.id, [draft.id]))
    assert AddExamQuestionsHandler(w.exams, w.bank, w.uow)(TEACHER, AddExamQuestions(w.exam.id, [t.id, q1.id])) == 1
    UpdateExamHandler(w.exams, w.bank, w.uow)(TEACHER, UpdateExam(w.exam.id, {"settings": {"points_by_type": {"mcq": 0.5}}}))
    assert {eq.question_id: eq.points for eq in w.exams.questions(w.exam.id)} == {q1.id: 0.5, t.id: 1.0}
    with pytest.raises(Invalid):
        UpdateExamHandler(w.exams, w.bank, w.uow)(TEACHER, UpdateExam(w.exam.id, {"settings": {"points_by_type": {"mcq": 0}}}))


def test_exam_from_document_keeps_part_and_number_order():
    doc = uuid.uuid4()
    q = [QuestionRef(id=uuid.uuid4(), organization_id=ORG, type=t, status=s, part=p, number=n, source_document_id=doc)
         for t, s, p, n in (("true_false", "approved", "2", 1), ("mcq", "approved", "1", 2), ("mcq", "rejected", "1", 1),
                            ("mcq", "approved", "1", 10), ("short_answer", "auto_approved", "3", 1))]
    w = World()
    w.bank = FakeBank(*q)
    handler = CreateExamFromDocumentHandler(w.exams, w.bank, FakeSubjects(), w.uow)
    with pytest.raises(Invalid):
        handler(TEACHER, CreateExamFromDocument(DocumentRef(doc, "de.docx", "processing")))
    r = handler(TEACHER, CreateExamFromDocument(DocumentRef(doc, "de.docx", "parsed", {"source_name": "THPT A", "detected": {"duration": 90}})))
    assert r["added"] == 4 and r["skipped"] == 1 and w.uow.commits == 0  # ingestion's command commits
    exam = w.exams.rows[r["exam_id"]]
    assert exam.title == "THPT A" and exam.source == "document" and exam.settings["duration_minutes"] == 90
    assert [w.bank.refs[eq.question_id].number for eq in w.exams.questions(exam.id)] == [2, 10, 1, 1]
    assert [eq.points for eq in w.exams.questions(exam.id)] == [0.25, 0.25, 1.0, 0.5]


# ------------------------------------------------------------------ assignments


def test_assignment_needs_questions_a_valid_window_and_targets():
    w = World(mcq())
    handler = CreateAssignmentHandler(w.exams, w.assignments, w.roster, w.uow)
    base = dict(exam_id=w.exam.id, open_at=NOW, close_at=NOW + timedelta(hours=1), duration_minutes=45)
    for bad, field in ((dict(close_at=NOW), "close_at"), (dict(duration_minutes=601), "duration_minutes"), (dict(max_attempts=21), "max_attempts"),
                       (dict(results_policy="sometimes"), "results_policy"), (dict(class_ids=[uuid.uuid4()]), "class_ids"),
                       (dict(user_ids=[uuid.uuid4()]), "user_ids"), ({}, "class_ids")):
        with pytest.raises(Invalid) as e:
            handler(TEACHER, CreateAssignment(**{**base, **bad}))
        assert field in e.value.fields
    a = handler(TEACHER, CreateAssignment(**base, class_ids=[CLASS], title="  Giữa kỳ "))
    assert a.title == "Giữa kỳ" and len(w.assignments.targets(a.id)) == 1
    empty = Exam(organization_id=ORG, title="Trống")
    w.exams.add(empty)
    with pytest.raises(Invalid):
        handler(TEACHER, CreateAssignment(**{**base, "exam_id": empty.id}, class_ids=[CLASS]))


def test_start_checks_window_target_and_attempts_left():
    w = World(mcq(), mcq())
    upcoming = w.assignment(open_at=NOW + timedelta(minutes=5))
    with pytest.raises(Conflict) as e:
        w.start(upcoming)
    assert e.value.code == "not_open"
    closed = w.assignment(open_at=NOW - timedelta(hours=2), close_at=NOW)
    with pytest.raises(Conflict) as e:
        w.start(closed)
    assert e.value.code == "closed"
    a = w.assignment(close_at=NOW + timedelta(minutes=20))
    with pytest.raises(NotFound):
        w.start(a, OTHER)  # not in the class
    with pytest.raises(NotFound):
        w.start(a, TEACHER)  # staff are not targeted, so the same answer — not a 403 on the role (ADR-02)
    att = w.start(a)
    assert w.start(a) == att  # resumed
    assert w.attempts.rows[att].deadline_at == NOW + timedelta(minutes=20)  # the window closes before the time limit
    assert w.attempts.rows[att].max_score == 0.5
    w.submit(att)
    with pytest.raises(Conflict) as e:
        w.start(a)
    assert e.value.code == "no_attempts_left"


def test_the_student_side_home_answers_staff_with_their_own_assignments():
    """exam-runner AC-07: a teacher is answered, not refused — and sees their own (nothing), never the student's."""
    w = World(mcq())
    a = w.assignment()
    home = MyAssignmentsHandler(w.assignments, w.attempts, w.exams, w.roster, w.clock)
    mine = home(STUDENT)
    assert [v.assignment.id for v in mine] == [a.id] and mine[0].state == "open" and mine[0].attempts_left == 1
    assert home(TEACHER) == []
    # the home screen groups by subject, so each row carries the subject of the exam behind it (none here)
    assert mine[0].subject_id is None
    w.exam.subject_id = uuid.uuid4()
    assert home(STUDENT)[0].subject_id == w.exam.subject_id


def test_results_visibility_follows_the_policy():
    att = Attempt(organization_id=ORG, exam_id=uuid.uuid4(), student_id=STUDENT.user_id, deadline_at=NOW, status="submitted")
    a = Assignment(organization_id=ORG, exam_id=att.exam_id, title="x", open_at=NOW - timedelta(hours=1), close_at=NOW + timedelta(hours=1),
                   duration_minutes=10, results_policy="after_close")
    assert not assignment_rules.results_visible(a, att, NOW) and assignment_rules.results_visible(a, att, NOW + timedelta(hours=1))
    assert assignment_rules.results_visible(a, att, NOW, score_only=True) and assignment_rules.results_visible(None, att, NOW)
    a.results_policy = "never"
    assert not assignment_rules.results_visible(a, att, NOW + timedelta(days=9))
    att.status = "in_progress"
    assert not assignment_rules.results_visible(None, att, NOW)


# ------------------------------------------------------------------ attempts


def test_orders_shuffle_inside_sections_and_are_repeatable_with_a_seed():
    rows = [(ExamQuestion(exam_id=uuid.uuid4(), question_id=q.id, position=i, points=1, section=s), q)
            for i, (q, s) in enumerate([(mcq(), "I"), (mcq(), "I"), (mcq(), "I"), (tf(), "II"), (tf(), "II")], start=1)]
    order, options = attempt_rules.orders(rows, True, True, random.Random(3))
    assert attempt_rules.orders(rows, True, True, random.Random(3)) == (order, options)
    sections = {str(eq.question_id): eq.section for eq, _ in rows}
    assert [sections[i] for i in order] == ["I", "I", "I", "II", "II"]
    assert set(options) == {str(eq.question_id) for eq, q in rows if q.type == "mcq"}
    assert attempt_rules.orders(rows, False, False) == ([str(eq.question_id) for eq, _ in rows], {})


def test_shuffled_options_are_shown_as_a_to_d_and_stored_in_the_original_labels():
    q = mcq(key="B")
    w = World(q)
    att_id = w.start(w.assignment(), rng=random.Random(5))
    shown = shown_key(w, att_id, q)
    saved = w.save(att_id, q.id, {"key": shown})
    assert w.attempts.answer(att_id, q.id).response == {"key": "B"} and saved["response"] == {"key": shown}
    with pytest.raises(Invalid):
        w.save(att_id, q.id, {"key": "Z"})
    with pytest.raises(NotFound):
        w.save(att_id, uuid.uuid4(), {"key": "A"})


def test_submit_grades_writes_facts_in_order_and_closes():
    q1, q2, t, e = mcq(), mcq(), tf(), essay()
    w = World(q1, q2, t, e)
    w.bank.topics = {q1.id: TOPIC_A}
    att_id = w.start(w.assignment())
    w.save(att_id, q1.id, {"key": shown_key(w, att_id, q1)})
    w.save(att_id, t.id, {"a": True, "b": False, "c": True, "d": False})  # 3 of 4
    w.save(att_id, e.id, {"text": "Bài làm"})
    with pytest.raises(Forbidden):
        w.submit(att_id, TEACHER)
    assert w.submit(att_id)["status"] == "submitted"
    att = w.attempts.rows[att_id]
    assert att.score == 0.25 + 0.5 and att.max_score == 0.25 * 2 + 1 + 1 and att.needs_grading is True and att.submitted_at == NOW
    assert w.attempts.answer(att_id, q1.id).key_snapshot == {"key": "B"}
    graded = [f.question_id for f in w.listener.facts]
    # the essay waits for a teacher, the second question was never answered (ADR-02)
    assert graded == [qid for qid in map(uuid.UUID, att.question_order) if qid not in (e.id, q2.id)]
    fact = w.facts.rows[(att_id, q1.id)]
    assert fact.topic_path == "dai_so" and fact.correct_ratio == 1.0 and fact.school_year_id == YEAR and fact.class_ids == [CLASS]
    assert fact.first_attempt is True
    with pytest.raises(Conflict) as closed:
        w.save(att_id, q1.id, {"key": "A"})
    assert closed.value.code == "attempt_closed"


def test_essay_grading_updates_the_total_and_its_fact():
    q, e = mcq(), essay()
    w = World(q, e)
    att_id = w.start(w.assignment())
    w.save(att_id, q.id, {"key": shown_key(w, att_id, q)})
    w.save(att_id, e.id, {"text": "Bài làm"})
    handler = GradeEssayHandler(w.attempts, w.bank, w.grading(), w.uow)
    with pytest.raises(Conflict) as early:
        handler(TEACHER, GradeEssay(att_id, e.id, 0.5))
    assert early.value.code == "not_submitted"
    w.submit(att_id)
    with pytest.raises(Forbidden):
        handler(STUDENT, GradeEssay(att_id, e.id, 1))
    with pytest.raises(Invalid) as bad:
        handler(TEACHER, GradeEssay(att_id, e.id, 1.5))
    assert bad.value.fields == {"points": "Điểm từ 0 đến 1.0"}
    assert handler(TEACHER, GradeEssay(att_id, e.id, 0.5, "Thiếu bước 2")) == {"score": 0.75, "needs_grading": False}
    ans = w.attempts.answer(att_id, e.id)
    assert ans.comment == "Thiếu bước 2" and ans.is_correct is False and ans.graded_by == TEACHER.user_id
    assert w.facts.rows[(att_id, e.id)].points == 0.5


def test_timing_accumulates_over_the_saves_and_is_clamped_to_the_attempt_window():
    q = mcq()
    w = World(q)
    att_id = w.start(w.assignment())
    w.clock.at = NOW + timedelta(seconds=30)
    w.save(att_id, q.id, {"key": "A"}, seconds=12, first_seen=NOW + timedelta(seconds=5))
    ans = w.attempts.answer(att_id, q.id)
    assert ans.seconds_spent == 12 and ans.save_count == 1 and ans.first_seen_at == NOW + timedelta(seconds=5)
    assert ans.answered_at == w.clock.at
    w.clock.at = NOW + timedelta(seconds=60)
    w.save(att_id, q.id, {"key": "B"}, seconds=-5, first_seen=NOW)  # nonsense costs nothing and the first sight stands
    assert ans.seconds_spent == 12 and ans.save_count == 2 and ans.first_seen_at == NOW + timedelta(seconds=5)
    w.save(att_id, q.id, {"key": "C"}, seconds=10_000)  # absurd: down to the window (started_at → now)
    assert ans.seconds_spent == 60 and ans.save_count == 3


def test_an_unanswered_question_scores_zero_and_leaves_no_fact():
    q, blank, never = mcq(), QuestionRef(id=uuid.uuid4(), organization_id=ORG, type="short_answer", status="approved",
                                         answer={"value": "2"}), mcq()
    w = World(q, blank, never)
    att_id = w.start(w.assignment())
    w.save(att_id, q.id, {"key": shown_key(w, att_id, q)})
    w.save(att_id, blank.id, {"value": "   "})  # opened, nothing written down
    w.submit(att_id)
    att = w.attempts.rows[att_id]
    assert set(w.facts.rows) == {(att_id, q.id)} and [f.question_id for f in w.listener.facts] == [q.id]
    assert w.attempts.answer(att_id, blank.id).points == 0.0 and w.attempts.answer(att_id, never.id).points == 0.0
    assert att.score == 0.25 and att.max_score == 0.25 * 2 + 0.5  # the blanks still count against the result


def test_an_abandoned_attempt_is_swept_without_any_fact():
    q = mcq()
    w = World(q)
    att_id = w.start(w.assignment())
    w.clock.at = NOW + timedelta(hours=3)
    assert SweepExpiredAttemptsHandler(w.attempts, w.grading(), w.clock)() == 1
    assert w.attempts.rows[att_id].status == "submitted" and w.attempts.rows[att_id].score == 0
    assert w.facts.rows == {} and w.listener.facts == []


def test_only_the_first_answer_of_a_question_is_a_first_attempt():
    q = mcq()
    w = World(q)
    a = w.assignment(max_attempts=2)
    first = w.start(a)
    w.save(first, q.id, {"key": shown_key(w, first, q)})
    w.submit(first)
    assert w.facts.rows[(first, q.id)].first_attempt is True
    w.clock.at = NOW + timedelta(minutes=5)
    second = w.start(a)
    w.clock.at = NOW + timedelta(minutes=6)
    w.save(second, q.id, {"key": shown_key(w, second, q)}, seconds=7)
    w.submit(second)
    fact = w.facts.rows[(second, q.id)]
    assert fact.first_attempt is False and fact.seconds_spent == 7 and fact.answered_at == NOW + timedelta(minutes=6)
    assert w.facts.rows[(first, q.id)].first_attempt is True


def test_an_empty_essay_scores_zero_without_waiting():
    e = essay()
    w = World(e)
    att_id = w.start(w.assignment())
    w.submit(att_id)
    att = w.attempts.rows[att_id]
    assert att.score == 0 and att.needs_grading is False


def test_deadline_closes_the_attempt_lazily_and_in_the_sweep():
    q = mcq()
    w = World(q)
    a = w.assignment()
    att_id = w.start(a)
    w.clock.at = NOW + timedelta(minutes=45, seconds=20)  # within grace: still open
    w.save(att_id, q.id, {"key": "A"})
    w.clock.at = NOW + timedelta(minutes=46)
    with pytest.raises(Conflict):
        w.save(att_id, q.id, {"key": "B"})
    att = w.attempts.rows[att_id]
    assert att.status == "submitted" and att.submitted_at == att.deadline_at + attempt_rules.GRACE  # dated at the deadline
    other = World(mcq())
    other_att = other.start(other.assignment())
    other.clock.at = NOW + timedelta(hours=3)
    assert SweepExpiredAttemptsHandler(other.attempts, other.grading(), other.clock)() == 1
    assert other.attempts.rows[other_att].status == "submitted"


def test_result_is_hidden_until_the_policy_allows_it():
    q = mcq()
    w = World(q)
    a = w.assignment(results_policy="after_close")
    att_id = w.start(a)
    w.save(att_id, q.id, {"key": shown_key(w, att_id, q)})
    w.submit(att_id)

    def result(actor):
        return AttemptResultHandler(w.attempts, w.assignments, w.exams, w.bank, w.grading(), w.clock, w.uow)(actor, AttemptResult(att_id))

    hidden = result(STUDENT)
    assert hidden["hidden"] is True and hidden["reason"] == "after_close" and hidden["score10"] == 10.0 and "questions" not in hidden
    assert result(TEACHER)["hidden"] is False
    w.clock.at = a.close_at
    shown = result(STUDENT)
    assert shown["hidden"] is False and shown["questions"][0]["is_correct"] is True
    assert shown["questions"][0]["answer"] == {"key": shown_key(w, att_id, q)} and shown["sections"] == [
        {"section": "I", "points": 0.25, "max_points": 0.25}]
    with pytest.raises(NotFound):
        AttemptResultHandler(w.attempts, w.assignments, w.exams, w.bank, w.grading(), w.clock, w.uow)(OTHER, AttemptResult(att_id))


def test_a_trial_run_reads_the_paper_grades_it_and_writes_nothing():
    """exam-runner AC-04, AC-05: the student's own paper, scored like a sitting, with not one row behind it (ADR-01)."""
    q, t, e = mcq(key="B"), tf(), essay()
    w = World(q, t, e)
    w.bank.topics = {q.id: TOPIC_A}
    a = w.assignment()
    paper = AssignmentPaperHandler(w.assignments, w.exams, w.bank)(TEACHER, AssignmentPaper(a.id))
    assert paper["title"] == a.title and paper["max_score"] == 2.25 and "deadline_at" not in paper
    assert [x["id"] for x in paper["questions"]] == [q.id, t.id, e.id]  # the exam's order, never shuffled
    assert all(x["answer"] is None and x["solution"] == "" and x["response"] is None for x in paper["questions"])
    assert [o["label"] for o in paper["questions"][0]["options"]] == ["A", "B", "C", "D"]
    assert all("is_true" not in o for o in paper["questions"][1]["options"])

    trial = TrialRunHandler(w.assignments, w.exams, w.bank, w.clock)(
        TEACHER, TrialRun(a.id, {q.id: {"key": "B"}, t.id: {"a": True, "b": False, "c": True, "d": False}, e.id: {"text": "Bài làm"}}))
    assert trial["score"] == 0.25 + 0.5 and trial["max_score"] == 2.25  # 3 of 4 statements: half the true/false points
    assert trial["id"] is None and trial["status"] == "submitted" and trial["hidden"] is False and trial["needs_grading"] is True
    assert trial["score10"] == scoring.scaled(0.75, 2.25) and trial["submitted_at"] == NOW
    graded = {x["id"]: x for x in trial["questions"]}
    assert graded[q.id]["is_correct"] is True and graded[q.id]["answer"] == {"key": "B"} and graded[q.id]["response"] == {"key": "B"}
    assert graded[e.id]["points"] is None and graded[t.id]["points"] == 0.5
    assert [x["topic"] for x in trial["topics"]] == ["Chưa phân loại", "Đại số"]  # weakest first
    assert trial["sections"] == [{"section": "I", "points": 0.25, "max_points": 0.25},
                                 {"section": "II", "points": 0.5, "max_points": 1.0},
                                 {"section": "IV", "points": 0.0, "max_points": 1.0}]
    assert w.attempts.rows == {} and w.attempts.answer_rows == {} and w.facts.rows == {}
    assert w.listener.facts == [] and w.uow.commits == 0
    with pytest.raises(Invalid):
        TrialRunHandler(w.assignments, w.exams, w.bank, w.clock)(TEACHER, TrialRun(a.id, {q.id: {"key": "Z"}}))


def test_answer_rules_bound_what_is_stored():
    t, q = tf(), QuestionRef(id=uuid.uuid4(), organization_id=ORG, type="short_answer", status="approved")
    assert attempt_rules.checked_response(t, {"a": True, "z": True, "b": "yes"}) == {"a": True}
    assert attempt_rules.checked_response(q, {"value": "x" * 150}) == {"value": "x" * 100}
    assert attempt_rules.checked_response(q, None) is None
    with pytest.raises(Invalid):
        attempt_rules.checked_response(q, "3")
    ans = AttemptAnswer(attempt_id=uuid.uuid4(), question_id=t.id, response={"a": True, "b": False, "c": True, "d": True})
    attempt_rules.grade_answer(ans, t, 1.0)
    assert ans.points == 1.0 and ans.is_correct is True and ans.max_points == 1.0
