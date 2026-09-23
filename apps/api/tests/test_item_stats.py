"""Item statistics over the graded answers: the question detail and the searchable columns
(learning-telemetry AC-03, AC-04, ADR-03). The facts are constructed so every number is exact."""
from datetime import timedelta
import uuid

from app.modules.assessment.domain.entities import AnswerFact, Attempt, AttemptAnswer
from app.modules.bank.domain.entities import Question
from app.shared.domain.clock import utcnow as now
from tests.exam_helpers import exam_with_questions
from tests.factories import PASSWORD, make_org, make_user

POINTS = 1.0


def mcq_questions(client, db):
    """An admin, a student of the same org and two multiple-choice questions of an exam."""
    admin, exam = exam_with_questions(client, db, mcq=2, tf=0, short=0)
    student = make_user(db, admin.organization, "hstk", role="student")
    db.commit()
    ids = [q["id"] for q in exam["questions"] if q["type"] == "mcq"]
    return admin, exam, student, ids[0], ids[1]


def answer(db, admin, exam, student, question_id, *, ratio=1.0, score=5.0, seconds=30, first=True, key="A"):
    """One submitted attempt with its answer and the fact it produced (an unanswered question leaves none)."""
    org_id, exam_id, qid = admin.organization_id, uuid.UUID(exam["id"]), uuid.UUID(question_id)
    att = Attempt(organization_id=org_id, exam_id=exam_id, student_id=student.id, deadline_at=now() + timedelta(hours=1),
                  started_at=now(), submitted_at=now(), status="submitted", score=score, max_score=10.0)
    db.add(att)
    db.flush()  # the answer and the fact point at it
    db.add(AttemptAnswer(attempt_id=att.id, question_id=qid, response=None if key is None else {"key": key},
                         is_correct=ratio == 1.0, points=POINTS * ratio, max_points=POINTS, seconds_spent=seconds or 0))
    db.add(AnswerFact(organization_id=org_id, attempt_id=att.id, exam_id=exam_id, student_id=student.id,
                      question_id=qid, qtype="mcq", points=POINTS * ratio, max_points=POINTS, correct_ratio=ratio,
                      seconds_spent=seconds, first_attempt=first, answered_at=now()))
    db.flush()
    return att


def stats(client, question_id):
    r = client.get(f"/api/questions/{question_id}/stats")
    assert r.status_code == 200, r.text
    return r.json()


def test_nine_answers_are_not_enough_data_the_tenth_is(client, db):
    admin, exam, student, qid, _ = mcq_questions(client, db)
    for i in range(9):
        answer(db, admin, exam, student, qid, ratio=1.0 if i < 6 else 0.0)
    db.commit()
    s = stats(client, qid)
    assert s["observations"] == 9 and s["enough_data"] is False
    assert [s["correct_ratio"], s["first_attempt_ratio"], s["discrimination"], s["median_seconds"]] == [None] * 4
    assert s["options"] == []
    answer(db, admin, exam, student, qid, ratio=1.0)
    db.commit()
    s = stats(client, qid)
    assert s["observations"] == 10 and s["enough_data"] is True and s["correct_ratio"] == 0.7


def test_a_question_nobody_answered_reports_zero_observations(client, db):
    _, _, _, qid, _ = mcq_questions(client, db)
    s = stats(client, qid)
    assert s == {"observations": 0, "enough_data": False, "correct_ratio": None, "first_attempt_ratio": None,
                 "discrimination": None, "median_seconds": None, "options": []}


def test_first_attempt_ratio_counts_only_first_attempts_and_the_median_ignores_missing_seconds(client, db):
    admin, exam, student, qid, _ = mcq_questions(client, db)
    # first attempts: 4 right of 8; the retries are all right and must not flatter the first-attempt share
    for i in range(8):
        answer(db, admin, exam, student, qid, ratio=1.0 if i < 4 else 0.0, seconds=10 * (i + 1))
    for _ in range(4):
        answer(db, admin, exam, student, qid, ratio=1.0, first=False, seconds=None)
    db.commit()
    s = stats(client, qid)
    assert s["observations"] == 12 and s["correct_ratio"] == 0.667 and s["first_attempt_ratio"] == 0.5
    assert s["median_seconds"] == 45  # over the eight answers that reported seconds (10…80), not the four without


def test_discrimination_is_positive_when_the_strongest_third_gets_it_right(client, db):
    admin, exam, student, good, bad = mcq_questions(client, db)
    for i in range(12):
        score = 10.0 if i < 4 else (5.0 if i < 8 else 1.0)  # four strong, four middling, four weak attempts
        answer(db, admin, exam, student, good, ratio=1.0 if i < 4 else (0.5 if i < 8 else 0.0), score=score)
        answer(db, admin, exam, student, bad, ratio=0.0 if i < 4 else (0.5 if i < 8 else 1.0), score=score)
    db.commit()
    assert stats(client, good)["discrimination"] == 1.0
    assert stats(client, bad)["discrimination"] == -1.0


def test_option_counts_come_from_the_responses_with_the_key_marked(client, db):
    admin, exam, student, qid, _ = mcq_questions(client, db)
    key = db.get(Question, qid).answer["key"]
    labels = [o["label"] for o in db.get(Question, qid).options]
    other = next(lab for lab in labels if lab != key)
    for i in range(10):
        answer(db, admin, exam, student, qid, ratio=1.0 if i < 6 else 0.0, key=key if i < 6 else other)
    db.commit()
    s = stats(client, qid)
    assert [o["label"] for o in s["options"]] == labels  # every option, in the question's own order
    by_label = {o["label"]: o for o in s["options"]}
    assert by_label[key] == {"label": key, "chosen": 6, "ratio": 0.6, "is_key": True}
    assert by_label[other] == {"label": other, "chosen": 4, "ratio": 0.4, "is_key": False}
    assert all(o["chosen"] == 0 and o["ratio"] == 0.0 for lab, o in by_label.items() if lab not in (key, other))


def test_another_organisation_sees_no_such_question(client, db):
    admin, exam, student, qid, _ = mcq_questions(client, db)
    for _ in range(10):
        answer(db, admin, exam, student, qid)
    other = make_org(db, code="trungtamb", name="Trung tâm B")
    make_user(db, other, "adminb", role="org_admin")
    db.commit()
    c = client.__class__(client.app)
    assert c.post("/api/auth/login", json={"org_code": "trungtamb", "username": "adminb", "password": PASSWORD}).status_code == 200
    r = c.get(f"/api/questions/{qid}/stats")
    assert r.status_code == 404 and r.json()["code"] == "not_found"


def test_the_bank_filters_and_sorts_by_the_observed_difficulty(client, db):
    admin, exam, student, easy, hard = mcq_questions(client, db)
    for i in range(10):
        answer(db, admin, exam, student, easy, ratio=1.0 if i < 8 else 0.0)
    for i in range(12):
        answer(db, admin, exam, student, hard, ratio=1.0 if i < 3 else 0.0)
    db.commit()

    def search(**body):
        r = client.post("/api/questions/search", json={"limit": 200, **body})
        assert r.status_code == 200, r.text
        return r.json()

    answered_ids = [q["id"] for q in search(filters={"stats_observations": {"operator": ">=", "value": 10}})["data"]]
    assert sorted(answered_ids) == sorted([easy, hard])
    assert [q["id"] for q in search(filters={"stats_observations": {"operator": ">", "value": 10}})["data"]] == [hard]
    weak = search(filters={"stats_correct_ratio": {"operator": "<", "value": 0.5}})["data"]
    assert [q["id"] for q in weak] == [hard]
    ranked = [q["id"] for q in search(sort=[{"field": "stats_correct_ratio", "desc": True}])["data"]]
    assert ranked[:2] == [easy, hard]  # unanswered questions sort last (no ratio)
    # a question nobody answered counts as zero observations, it is not lost
    assert search(filters={"stats_observations": {"operator": "<", "value": 10}})["total"] == search()["total"] - 2


def test_unknown_operator_and_unknown_column_are_refused(client, db):
    mcq_questions(client, db)
    r = client.post("/api/questions/search", json={"filters": {"stats_correct_ratio": {"operator": "*", "value": "x"}}})
    assert r.status_code == 422 and r.json()["code"] == "bad_filter"
    r = client.post("/api/questions/search", json={"filters": {"stats_median_seconds": {"value": 1}}})
    assert r.status_code == 422 and r.json()["code"] == "bad_filter"
    r = client.post("/api/questions/search", json={"sort": [{"field": "stats_discrimination"}]})
    assert r.status_code == 422 and r.json()["code"] == "bad_sort"
