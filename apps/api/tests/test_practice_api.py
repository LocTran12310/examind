from datetime import timedelta

from sqlalchemy import select

from app.shared.domain.clock import utcnow as now
from app.shared.infrastructure.schema.assessment import attempts, exams
from tests.exam_helpers import display_key, klass_with_student, login
from tests.test_mastery import take


def test_student_practice_flow_updates_mastery(client, db):
    take(client, db, right=False)
    s = login(client, "trungtama", "hs01")
    before = {r["topic_id"]: r["mastery"] for r in s.get("/api/me/mastery").json() if r["tracked"]}
    r = s.post("/api/me/practice", json={"count": 10})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["question_count"] == 10 and body["groups"]
    att = body["attempt_id"]
    view = s.get(f"/api/attempts/{att}").json()
    assert len(view["questions"]) == 10 and view["assignment_id"] is None
    for q in view["questions"]:
        if q["type"] == "mcq":
            s.put(f"/api/attempts/{att}/answers/{q['id']}", json={"response": display_key(db, q)})
    s.post(f"/api/attempts/{att}/submit")
    result = s.get(f"/api/attempts/{att}/result").json()
    assert result["hidden"] is False and result["score10"] > 0
    after = {r["topic_id"]: r["mastery"] for r in s.get("/api/me/mastery").json() if r["tracked"]}
    assert any(after[k] > before.get(k, 0) for k in after)
    history = s.get("/api/me/practice").json()
    assert history[0]["attempt_id"] == att and history[0]["score10"] == result["score10"]
    assert all(e["source"] != "adaptive" for e in client.post("/api/exams/search", json={}).json()["data"])


def test_teacher_assigns_personal_review_to_class(client, db):
    admin = take(client, db, right=False)
    klass = client.post("/api/classes/search", json={}).json()["data"][0]
    klass2, _ = klass_with_student(client, db, admin, "hs02")
    client.post(f"/api/classes/{klass['id']}/members", json={"user_ids": [client.post('/api/users/search', json={'q': 'hs02'}).json()['data'][0]['id']]})
    r = client.post(f"/api/classes/{klass['id']}/adaptive-assignments",
                    json={"count": 10, "open_at": (now() - timedelta(minutes=1)).isoformat(), "close_at": (now() + timedelta(days=1)).isoformat(), "duration_minutes": 30})
    assert r.json() == {"created": 2}
    for username in ("hs01", "hs02"):
        s = login(client, "trungtama", username)
        mine = [x for x in s.get("/api/me/assignments").json() if x["assignment"]["title"] == "Đề ôn cá nhân"]
        assert len(mine) == 1 and mine[0]["state"] == "open"
    ov = client.get(f"/api/classes/{klass['id']}/overview").json()
    assert all(o["review"] and o["review"]["status"] == "not_started" for o in ov)
    # the cell has to answer four questions, not one: which paper, given when, due when, and how many in all
    assert all(o["review"]["title"] == "Đề ôn cá nhân" and o["review"]["open_at"] and o["review"]["close_at"] for o in ov)
    assert all(o["review"]["total"] == 1 for o in ov)
    # give the class a second round: the newest paper is the one shown, and the count says it is not alone.
    # Counting rows in Python after `limit(1)` would answer 1 here — which is the whole point of the window (ADR-02)
    client.post(f"/api/classes/{klass['id']}/adaptive-assignments",
                json={"count": 10, "open_at": now().isoformat(), "close_at": (now() + timedelta(days=3)).isoformat(), "duration_minutes": 30})
    ov2 = client.get(f"/api/classes/{klass['id']}/overview").json()
    assert all(o["review"]["total"] == 2 for o in ov2)
    assert {o["review"]["assignment_id"] for o in ov2}.isdisjoint({o["review"]["assignment_id"] for o in ov})
    assert login(client, "trungtama", "hs01").post(f"/api/classes/{klass['id']}/adaptive-assignments", json={
        "count": 5, "open_at": now().isoformat(), "close_at": (now() + timedelta(days=1)).isoformat()}).status_code == 403


def test_practice_exam_records_the_subject_it_was_drawn_inside(client, db):
    """The plan is built inside one subject, so the exam says which one (ADR-01) — nobody has to read the
    questions back to find out. Asked without a subject, the exam records none rather than guessing."""
    take(client, db, right=False)
    s = login(client, "trungtama", "hs01")
    subject = client.get("/api/taxonomy").json()["subjects"][0]["id"]

    def subject_of(attempt_id: str):
        exam_id = db.scalar(select(attempts.c.exam_id).where(attempts.c.id == attempt_id))
        return db.scalar(select(exams.c.subject_id).where(exams.c.id == exam_id))

    scoped = s.post("/api/me/practice", json={"count": 5, "subject_id": subject}).json()
    plain = s.post("/api/me/practice", json={"count": 5}).json()
    assert str(subject_of(scoped["attempt_id"])) == subject
    assert subject_of(plain["attempt_id"]) is None

    # and the two lists a student narrows by subject say which subject each row is (ADR-03): without that, a
    # picker on the progress page could only ever narrow half the screen
    history = {h["attempt_id"]: h["subject_id"] for h in s.get("/api/me/practice").json()}
    assert history[scoped["attempt_id"]] == subject
    assert history[plain["attempt_id"]] is None  # asked without one: not claimed by any subject
    assert all("subject_id" in row for row in s.get("/api/me/mastery").json())
