from datetime import timedelta
import uuid

from sqlalchemy import func, select

from app.modules.analytics.domain.entities import TopicMastery
from app.modules.assessment.domain.entities import AnswerFact, Attempt, AttemptAnswer, ExamQuestion
from tests.exam_helpers import assign, display_key, exam_with_questions, key_of, klass_with_student, login


def rows_written(db) -> dict:
    """What a sitting leaves behind — the four tables a trial run must not touch (exam-runner ADR-01)."""
    return {t.__name__: db.scalar(select(func.count()).select_from(t)) for t in (Attempt, AttemptAnswer, AnswerFact, TopicMastery)}


def test_assign_home_and_start(client, db):
    admin, exam = exam_with_questions(client, db)
    klass, student = klass_with_student(client, db, admin)
    a = assign(client, exam["id"], klass["id"], results_policy="after_submit")
    assert a["students"] == 1
    s = login(client, "trungtama", "hs01")
    home = s.get("/api/me/assignments").json()
    assert [x["state"] for x in home] == ["open"] and home[0]["attempts_left"] == 1
    r = s.post(f"/api/assignments/{a['id']}/start")
    assert r.status_code == 200
    att = r.json()["attempt_id"]
    assert s.post(f"/api/assignments/{a['id']}/start").json()["attempt_id"] == att  # resumed
    listed = client.post("/api/assignments/search", json={"filters": {"exam_id": {"value": exam["id"]}}}).json()["data"]
    assert listed[0]["classes"] == [klass["name"]] and listed[0]["students"] == 1


def test_window_and_attempt_limits(client, db):
    admin, exam = exam_with_questions(client, db)
    klass, _ = klass_with_student(client, db, admin)
    later = assign(client, exam["id"], klass["id"], open_delta=3600, close_delta=7200)
    s = login(client, "trungtama", "hs01")
    r = s.post(f"/api/assignments/{later['id']}/start")
    assert r.status_code == 409 and r.json()["code"] == "not_open"
    assert s.get("/api/me/assignments").json()[0]["state"] == "upcoming"
    now_a = assign(client, exam["id"], klass["id"])
    att = s.post(f"/api/assignments/{now_a['id']}/start").json()["attempt_id"]
    s.post(f"/api/attempts/{att}/submit")
    r = s.post(f"/api/assignments/{now_a['id']}/start")
    assert r.status_code == 409 and r.json()["code"] == "no_attempts_left"


def test_the_student_side_endpoints_answer_staff(client, db):
    """exam-runner AC-07: roles nest, so a teacher is answered like anyone else — with their own data."""
    admin, exam = exam_with_questions(client, db)
    klass, _ = klass_with_student(client, db, admin)
    a = assign(client, exam["id"], klass["id"])
    assert client.get("/api/me/assignments").json() == []  # answered, and nothing of the student's
    assert client.post(f"/api/assignments/{a['id']}/start").status_code == 404  # not targeted; a trial is the way in
    s = login(client, "trungtama", "hs01")
    home = s.get("/api/me/assignments").json()
    assert [x["state"] for x in home] == ["open"]  # the student is untouched
    assert s.post(f"/api/assignments/{a['id']}/start").status_code == 200


def test_the_paper_is_the_student_view_with_nothing_behind_it(client, db):
    """exam-runner AC-04: the same stripping as the runner (ADR-04), the exam's order, no timer and no attempt."""
    admin, exam = exam_with_questions(client, db)
    klass, _ = klass_with_student(client, db, admin)
    a = assign(client, exam["id"], klass["id"], title="Kiểm tra giữa kỳ")
    paper = client.get(f"/api/assignments/{a['id']}/paper").json()
    assert paper["title"] == "Kiểm tra giữa kỳ" and paper["assignment_id"] == a["id"]
    assert paper["max_score"] == exam["total_points"] and "deadline_at" not in paper and "id" not in paper
    assert len(paper["questions"]) == exam["question_count"]
    assert all(q["answer"] is None and q["solution"] == "" for q in paper["questions"])
    assert all("is_true" not in o for q in paper["questions"] for o in q["options"])
    assert all(q["response"] is None for q in paper["questions"])
    by_position = db.scalars(select(ExamQuestion.question_id).where(ExamQuestion.exam_id == exam["id"]).order_by(ExamQuestion.position)).all()
    assert [q["id"] for q in paper["questions"]] == [str(i) for i in by_position]  # the exam's order, never shuffled
    assert [q["number"] for q in paper["questions"]] == list(range(1, exam["question_count"] + 1))
    s = login(client, "trungtama", "hs01")
    assert s.get(f"/api/assignments/{a['id']}/paper").status_code == 403  # the paper is for whoever set the exam
    assert client.get(f"/api/assignments/{uuid.uuid4()}/paper").status_code == 404


def test_a_trial_run_is_scored_and_writes_nothing(client, db):
    """exam-runner AC-05 / ADR-01: the teacher gets a score and the class report cannot tell it ever happened."""
    admin, exam = exam_with_questions(client, db)
    klass, _ = klass_with_student(client, db, admin)
    a = assign(client, exam["id"], klass["id"])
    s = login(client, "trungtama", "hs01")
    att = s.post(f"/api/assignments/{a['id']}/start").json()["attempt_id"]
    sat = next(q for q in s.get(f"/api/attempts/{att}").json()["questions"] if q["type"] == "mcq")
    s.put(f"/api/attempts/{att}/answers/{sat['id']}", json={"response": display_key(db, sat)})
    s.post(f"/api/attempts/{att}/submit")
    db.expire_all()
    before, report_before = rows_written(db), client.get(f"/api/assignments/{a['id']}/report").json()
    assert before["Attempt"] == 1 and before["AnswerFact"] > 0  # there is something a trial could disturb

    paper = client.get(f"/api/assignments/{a['id']}/paper").json()
    responses, expected = {}, 0.0
    for q in paper["questions"]:
        if q["type"] == "mcq":
            responses[q["id"]] = display_key(db, q)
        elif q["type"] == "true_false":
            responses[q["id"]] = key_of(db, q["id"])
        else:
            continue
        expected += q["points"]
    r = client.post(f"/api/assignments/{a['id']}/trial", json={"responses": responses}).json()
    assert abs(r["score"] - expected) < 1e-6 and r["max_score"] == exam["total_points"]
    assert r["id"] is None and r["status"] == "submitted" and r["hidden"] is False and r["needs_grading"] is False
    assert r["score10"] == round(expected / exam["total_points"] * 10, 2)
    assert all(q["answer"] for q in r["questions"]) and sum(q["max_points"] for q in r["questions"]) == exam["total_points"]
    assert [q["number"] for q in r["questions"]] == [q["number"] for q in paper["questions"]]

    db.expire_all()
    assert rows_written(db) == before
    assert client.get(f"/api/assignments/{a['id']}/report").json() == report_before


def test_a_trial_run_is_staff_only_and_checks_its_answers(client, db):
    admin, exam = exam_with_questions(client, db)
    klass, _ = klass_with_student(client, db, admin)
    a = assign(client, exam["id"], klass["id"])
    mcq = next(q for q in client.get(f"/api/assignments/{a['id']}/paper").json()["questions"] if q["type"] == "mcq")
    assert client.post(f"/api/assignments/{a['id']}/trial", json={"responses": {mcq["id"]: {"key": "Z"}}}).status_code == 422
    empty = client.post(f"/api/assignments/{a['id']}/trial", json={}).json()
    assert empty["score"] == 0 and len(empty["questions"]) == exam["question_count"]  # no answers is a valid trial
    s = login(client, "trungtama", "hs01")
    assert s.post(f"/api/assignments/{a['id']}/trial", json={"responses": {}}).status_code == 403
    assert client.post(f"/api/assignments/{uuid.uuid4()}/trial", json={"responses": {}}).status_code == 404
    assert rows_written(db) == {"Attempt": 0, "AttemptAnswer": 0, "AnswerFact": 0, "TopicMastery": 0}


def test_validation_and_permissions(client, db):
    admin, exam = exam_with_questions(client, db)
    klass, _ = klass_with_student(client, db, admin)
    r = client.post("/api/assignments", json={"exam_id": exam["id"], "open_at": "2026-09-22T10:00:00Z", "close_at": "2026-09-22T09:00:00Z",
                                                "duration_minutes": 10, "class_ids": [klass["id"]]})
    assert r.status_code == 422
    empty = client.post("/api/exams", json={"title": "Trống"}).json()
    assert client.post("/api/assignments", json={"exam_id": empty["id"], "open_at": "2026-09-22T08:00:00Z", "close_at": "2026-09-22T09:00:00Z",
                                                 "duration_minutes": 10, "class_ids": [klass["id"]]}).status_code == 422
    a = assign(client, exam["id"], klass["id"])
    s = login(client, "trungtama", "hs01")
    assert s.post("/api/assignments/search", json={}).status_code == 403
    outsider = klass_with_student(client, db, admin, "hs02")[1]
    o = login(client, "trungtama", "hs02")
    assert o.post(f"/api/assignments/{a['id']}/start").status_code == 404
    assert outsider  # member of another class only


def _sit(session, assignment_id, db, minutes_late=None):
    """Start, answer one multiple-choice question, submit — optionally backdating the start so the sitting has a
    duration to report. Backdating is the only way to give it one: `started_at` is written server-side."""
    attempt = session.post(f"/api/assignments/{assignment_id}/start").json()["attempt_id"]
    if minutes_late is not None:
        row = db.get(Attempt, uuid.UUID(attempt))
        row.started_at = row.started_at - timedelta(minutes=minutes_late)
        db.commit()
    view = session.get(f"/api/attempts/{attempt}").json()
    q = next(x for x in view["questions"] if x["type"] == "mcq")
    session.put(f"/api/attempts/{attempt}/answers/{q['id']}", json={"response": display_key(db, q)})
    session.post(f"/api/attempts/{attempt}/submit")
    return attempt


def test_attempt_history_says_which_paper_when_and_how_long(client, db):
    """AC-01. `minutes` is the wall clock of the whole sitting — `submitted_at - started_at` — and not the sum of
    the per-question seconds, which measures a different thing and is clamped to this same window (F14 ADR-01)."""
    admin, exam = exam_with_questions(client, db)
    klass, student = klass_with_student(client, db, admin)
    a = assign(client, exam["id"], klass["id"])
    s = login(client, "trungtama", "hs01")
    _sit(s, a["id"], db, minutes_late=25)

    rows = client.post("/api/attempts/search", json={"filters": {"student_id": {"value": str(student.id)}}}).json()
    assert rows["total"] == 1
    row = rows["data"][0]
    assert row["exam_title"] == exam["title"] and row["assignment_title"] == a["title"]
    assert row["username"] == "hs01" and row["student_name"] == "Học Sinh"
    assert row["status"] == "submitted" and row["auto_submitted"] is False
    assert row["minutes"] == 25, "số phút là hiệu giờ treo tường của cả lượt"
    assert row["submitted_at"] is not None and row["score10"] is not None


def test_a_sitting_still_open_has_no_duration_yet(client, db):
    """`minutes` and `submitted_at` are null while the paper is still being sat — a zero there would read as
    "finished instantly" and that is a different claim."""
    admin, exam = exam_with_questions(client, db)
    klass, _ = klass_with_student(client, db, admin)
    a = assign(client, exam["id"], klass["id"])
    login(client, "trungtama", "hs01").post(f"/api/assignments/{a['id']}/start")

    row = client.post("/api/attempts/search", json={}).json()["data"][0]
    assert row["status"] == "in_progress" and row["submitted_at"] is None and row["minutes"] is None


def test_a_sitting_the_system_closed_is_marked_as_such(client, db):
    """AC-02. Hiding it would make the duration column lie about exactly the sittings worth looking at."""
    admin, exam = exam_with_questions(client, db)
    klass, _ = klass_with_student(client, db, admin)
    a = assign(client, exam["id"], klass["id"])
    s = login(client, "trungtama", "hs01")
    attempt = _sit(s, a["id"], db)
    row = db.get(Attempt, uuid.UUID(attempt))
    row.submitted_at = row.deadline_at + timedelta(seconds=30)  # what the expiry sweep writes
    db.commit()

    got = client.post("/api/attempts/search", json={}).json()["data"][0]
    assert got["auto_submitted"] is True


def test_a_student_reads_only_their_own_sittings(client, db):
    """The scope comes from the caller, never from the body. F20 is why this is a test and not a comment: a page
    called "của tôi" once answered with the whole organisation's numbers."""
    admin, exam = exam_with_questions(client, db)
    klass, mine = klass_with_student(client, db, admin, username="hs01")
    other_class, other = klass_with_student(client, db, admin, username="hs02")
    for c, u in ((klass, mine), (other_class, other)):
        a = assign(client, exam["id"], c["id"])
        _sit(login(client, "trungtama", u.username), a["id"], db)

    assert client.post("/api/attempts/search", json={}).json()["total"] == 2  # staff see the organisation
    s = login(client, "trungtama", "hs01")
    asked_for_the_other = s.post("/api/attempts/search", json={"filters": {"student_id": {"value": str(other.id)}}}).json()
    assert asked_for_the_other["total"] == 1
    assert {r["username"] for r in asked_for_the_other["data"]} == {"hs01"}, "yêu cầu bị ép về chính người gọi"
