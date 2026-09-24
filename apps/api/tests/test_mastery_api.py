from tests.exam_helpers import login
from tests.test_mastery import ENOUGH, take


def test_mastery_endpoints(client, db):
    take(client, db, right=True, rounds=ENOUGH)
    s = login(client, "trungtama", "hs01")
    rows = s.get("/api/me/mastery").json()
    tracked = [r for r in rows if r["tracked"]]
    assert tracked and all(r["mastery"] > 0.5 for r in tracked)
    assert all(r["enough_data"] and not r["weak"] for r in tracked)  # answered enough, and answered right
    parents = [r for r in rows if not r["tracked"]]
    assert all(p["answers"] >= 1 for p in parents)
    # roles nest (exam-runner-and-roles ADR-02): staff may ask for their own rows and get their own — empty,
    # because nobody assigns them work. A student's rows are still a different question: /students/{id}/mastery
    assert client.get("/api/me/mastery").json() == []
    student_id = s.get("/api/auth/me").json()["id"]
    assert client.get(f"/api/students/{student_id}/mastery").json() == rows
    assert s.get(f"/api/students/{student_id}/mastery").status_code == 403
    klass = client.post("/api/classes/search", json={}).json()["data"][0]
    ov = client.get(f"/api/classes/{klass['id']}/overview").json()
    assert ov[0]["username"] == "hs01" and ov[0]["weakest"] == [] and ov[0]["review"] is None


def test_a_topic_with_too_few_answers_is_chua_du_du_lieu_not_weak(client, db):
    take(client, db, right=False)  # one sitting: every topic stays under the minimum (AC-05)
    s = login(client, "trungtama", "hs01")
    tracked = [r for r in s.get("/api/me/mastery").json() if r["tracked"]]
    assert tracked and all(r["mastery"] < 0.5 and r["answers"] < ENOUGH for r in tracked)
    assert all(not r["enough_data"] and not r["weak"] for r in tracked)
    klass = client.post("/api/classes/search", json={}).json()["data"][0]
    assert client.get(f"/api/classes/{klass['id']}/overview").json()[0]["weakest"] == []


def test_enough_wrong_answers_make_a_topic_weak_everywhere(client, db):
    take(client, db, right=False, rounds=ENOUGH)
    s = login(client, "trungtama", "hs01")
    tracked = [r for r in s.get("/api/me/mastery").json() if r["tracked"]]
    assert tracked and all(r["enough_data"] and r["weak"] for r in tracked)
    klass = client.post("/api/classes/search", json={}).json()["data"][0]
    weakest = client.get(f"/api/classes/{klass['id']}/overview").json()[0]["weakest"]
    assert weakest and all(w["mastery"] < 0.6 and w["answers"] >= ENOUGH for w in weakest)
    plan = s.post("/api/me/practice", json={"count": 10}).json()
    assert any(g["reason"] == "Chuyên đề yếu" for g in plan["groups"])
