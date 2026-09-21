from datetime import timedelta

from app.core.security import now
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
    assert all(e["source"] != "adaptive" for e in client.get("/api/exams").json())


def test_teacher_assigns_personal_review_to_class(client, db):
    admin = take(client, db, right=False)
    klass = client.get("/api/classes").json()[0]
    klass2, _ = klass_with_student(client, db, admin, "hs02")
    client.post(f"/api/classes/{klass['id']}/members", json={"user_ids": [client.get('/api/users', params={'q': 'hs02'}).json()['items'][0]['id']]})
    r = client.post(f"/api/classes/{klass['id']}/adaptive-assignments",
                    json={"count": 10, "open_at": (now() - timedelta(minutes=1)).isoformat(), "close_at": (now() + timedelta(days=1)).isoformat(), "duration_minutes": 30})
    assert r.json() == {"created": 2}
    for username in ("hs01", "hs02"):
        s = login(client, "trungtama", username)
        mine = [x for x in s.get("/api/me/assignments").json() if x["assignment"]["title"] == "Đề ôn cá nhân"]
        assert len(mine) == 1 and mine[0]["state"] == "open"
    ov = client.get(f"/api/classes/{klass['id']}/overview").json()
    assert all(o["review"] and o["review"]["status"] == "not_started" for o in ov)
    assert login(client, "trungtama", "hs01").post(f"/api/classes/{klass['id']}/adaptive-assignments", json={
        "count": 5, "open_at": now().isoformat(), "close_at": (now() + timedelta(days=1)).isoformat()}).status_code == 403
