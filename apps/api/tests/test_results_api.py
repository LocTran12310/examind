from datetime import timedelta

from app.modules.assessment.domain.entities import Assignment
from app.shared.domain.clock import utcnow as now
from tests.exam_helpers import assign, display_key, exam_with_questions, klass_with_student, login


def take(client, db, policy="after_submit", essay=False):
    admin, exam = exam_with_questions(client, db, essay=essay)
    klass, _ = klass_with_student(client, db, admin)
    a = assign(client, exam["id"], klass["id"], results_policy=policy)
    s = login(client, "trungtama", "hs01")
    att = s.post(f"/api/assignments/{a['id']}/start").json()["attempt_id"]
    for q in s.get(f"/api/attempts/{att}").json()["questions"]:
        if q["type"] == "mcq":
            s.put(f"/api/attempts/{att}/answers/{q['id']}", json={"response": display_key(db, q)})
        if q["type"] == "essay":
            s.put(f"/api/attempts/{att}/answers/{q['id']}", json={"response": {"text": "Bài làm của em"}})
    s.post(f"/api/attempts/{att}/submit")
    return admin, exam, a, s, att


def test_result_after_submit_has_feedback_and_breakdowns(client, db):
    _, exam, _, s, att = take(client, db)
    r = s.get(f"/api/attempts/{att}/result").json()
    assert r["hidden"] is False and r["max_score"] == exam["total_points"]
    assert r["score10"] == round(r["score"] / r["max_score"] * 10, 2)
    mcq = [q for q in r["questions"] if q["type"] == "mcq"]
    assert all(q["is_correct"] and q["response"] == q["answer"] for q in mcq)
    assert all("solution" in q for q in r["questions"])
    assert {x["section"] for x in r["sections"]} == {"I", "II", "III"}
    assert r["topics"] and r["topics"][0]["max_points"] > 0


def test_after_close_and_never_hide_details(client, db):
    _, _, a, s, att = take(client, db, policy="after_close")
    r = s.get(f"/api/attempts/{att}/result").json()
    assert r["hidden"] is True and r["reason"] == "after_close" and "questions" not in r and r["score10"] is not None
    assert client.get(f"/api/attempts/{att}/result").json()["hidden"] is False  # teachers always see
    row = db.get(Assignment, a["id"])
    row.open_at, row.close_at = now() - timedelta(hours=2), now() - timedelta(minutes=1)
    db.commit()
    assert s.get(f"/api/attempts/{att}/result").json()["hidden"] is False


def test_essay_grading_updates_total(client, db):
    _, exam, _, s, att = take(client, db, essay=True)
    r = s.get(f"/api/attempts/{att}/result").json()
    essay = next(q for q in r["questions"] if q["type"] == "essay")
    assert r["needs_grading"] is True and essay["points"] is None
    home = s.get("/api/me/assignments").json()[0]["attempts"][0]
    assert home["needs_grading"] is True
    bad = client.patch(f"/api/attempts/{att}/answers/{essay['id']}/grade", json={"points": 5})
    assert bad.status_code == 422
    g = client.patch(f"/api/attempts/{att}/answers/{essay['id']}/grade", json={"points": 0.5, "comment": "Thiếu bước 2"}).json()
    assert g["needs_grading"] is False and abs(g["score"] - (r["score"] + 0.5)) < 1e-9
    after = s.get(f"/api/attempts/{att}/result").json()
    essay2 = next(q for q in after["questions"] if q["type"] == "essay")
    assert essay2["points"] == 0.5 and essay2["comment"] == "Thiếu bước 2"
    assert s.patch(f"/api/attempts/{att}/answers/{essay['id']}/grade", json={"points": 1}).status_code == 403


def test_snapshot_survives_question_edit_and_blocks_delete(client, db):
    _, _, _, s, att = take(client, db)
    before = s.get(f"/api/attempts/{att}/result").json()
    q = next(x for x in before["questions"] if x["type"] == "mcq")
    other = next(o["label"] for o in q["options"] if o["label"] != q["answer"]["key"])
    assert client.patch(f"/api/questions/{q['id']}", json={"answer": {"key": other}}).status_code == 200
    after = s.get(f"/api/attempts/{att}/result").json()
    same = next(x for x in after["questions"] if x["id"] == q["id"])
    assert same["answer"] == q["answer"] and same["is_correct"] is True and after["score"] == before["score"]
    assert client.delete(f"/api/questions/{q['id']}").status_code == 409
