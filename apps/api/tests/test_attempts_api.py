from datetime import timedelta

from sqlalchemy import select

from app.core.security import now
from app.models import AnswerFact, Attempt
from tests.exam_helpers import assign, display_key, exam_with_questions, key_of, klass_with_student, login


def started(client, db, **kw):
    admin, exam = exam_with_questions(client, db, **kw)
    klass, student = klass_with_student(client, db, admin)
    a = assign(client, exam["id"], klass["id"], **{k: v for k, v in kw.items() if k in ("minutes",)})
    s = login(client, "trungtama", "hs01")
    att = s.post(f"/api/assignments/{a['id']}/start").json()["attempt_id"]
    return admin, exam, a, s, att


def test_student_view_hides_keys_and_restores_answers(client, db):
    _, exam, _, s, att = started(client, db)
    view = s.get(f"/api/attempts/{att}").json()
    assert len(view["questions"]) == exam["question_count"]
    assert all(q["answer"] is None and q["solution"] == "" for q in view["questions"])
    assert all("is_true" not in o for q in view["questions"] for o in q["options"])
    assert [q["section"] for q in view["questions"]] == sorted(q["section"] for q in view["questions"])
    mcq = next(q for q in view["questions"] if q["type"] == "mcq")
    assert s.put(f"/api/attempts/{att}/answers/{mcq['id']}", json={"response": {"key": "B"}}).status_code == 200
    assert s.put(f"/api/attempts/{att}/answers/{mcq['id']}", json={"response": {"key": "Z"}}).status_code == 422
    again = s.get(f"/api/attempts/{att}").json()
    assert next(q for q in again["questions"] if q["id"] == mcq["id"])["response"] == {"key": "B"}
    assert s.post(f"/api/attempts/{att}/tab-switch").json()["tab_switches"] == 1


def test_submit_grades_and_writes_facts(client, db):
    _, exam, _, s, att = started(client, db)
    view = s.get(f"/api/attempts/{att}").json()
    expected = 0.0
    for q in view["questions"]:
        key = key_of(db, q["id"])
        if q["type"] == "mcq":
            s.put(f"/api/attempts/{att}/answers/{q['id']}", json={"response": display_key(db, q)})
            expected += q["points"]
        elif q["type"] == "true_false":
            wrong_one = dict(key)
            first = next(iter(wrong_one))
            wrong_one[first] = not wrong_one[first]
            s.put(f"/api/attempts/{att}/answers/{q['id']}", json={"response": wrong_one})
            expected += q["points"] * 0.5  # 3 of 4 correct
        # short answer left empty
    r = s.post(f"/api/attempts/{att}/submit").json()
    assert r["status"] == "submitted"
    db.expire_all()
    a = db.get(Attempt, att)
    assert abs(a.score - expected) < 1e-6 and a.max_score == exam["total_points"]
    facts = db.scalars(select(AnswerFact).where(AnswerFact.attempt_id == a.id)).all()
    assert len(facts) == exam["question_count"] and all(f.topic_path for f in facts if f.qtype == "mcq")
    assert s.put(f"/api/attempts/{att}/answers/{view['questions'][0]['id']}", json={"response": {"key": "A"}}).status_code == 409


def test_deadline_is_enforced_and_swept(client, db):
    _, _, _, s, att = started(client, db)
    a = db.get(Attempt, att)
    a.deadline_at = now() - timedelta(minutes=5)
    db.commit()
    q = s.get(f"/api/attempts/{att}").json()  # lazy finalisation on access
    assert q["status"] == "submitted"
    assert s.post(f"/api/attempts/{att}/tab-switch").json()["tab_switches"] == 0  # closed attempts ignore events


def test_sweep_closes_abandoned_attempts(client, db):
    _, _, _, s, att = started(client, db)
    a = db.get(Attempt, att)
    a.deadline_at = now() - timedelta(minutes=5)
    db.commit()
    from app.services.attempts import sweep_expired

    assert sweep_expired(db) == 1
    db.commit()
    db.expire_all()
    assert db.get(Attempt, att).status == "submitted"


def test_other_students_cannot_see_attempt(client, db):
    admin, _, _, s, att = started(client, db)
    klass_with_student(client, db, admin, "hs09")
    other = login(client, "trungtama", "hs09")
    assert other.get(f"/api/attempts/{att}").status_code == 404
    assert other.put(f"/api/attempts/{att}/answers/x", json={"response": None}).status_code in (404, 422)
    assert client.get(f"/api/attempts/{att}").status_code == 200  # teacher


def test_shuffled_options_are_relabelled_for_students(client, db):
    from app.models import Question

    _, _, _, s, att = started(client, db)
    a = db.get(Attempt, att)
    view = s.get(f"/api/attempts/{att}").json()
    q = next(x for x in view["questions"] if x["type"] == "mcq")
    assert [o["label"] for o in q["options"]] == ["A", "B", "C", "D"]
    original = db.get(Question, q["id"])
    order = a.option_orders[q["id"]]
    key_display = "ABCD"[order.index(original.answer["key"])]
    assert next(o for o in q["options"] if o["label"] == key_display)["content"] == next(o["content"] for o in original.options if o["label"] == original.answer["key"])
    s.put(f"/api/attempts/{att}/answers/{q['id']}", json={"response": {"key": key_display}})
    s.post(f"/api/attempts/{att}/submit")
    r = s.get(f"/api/attempts/{att}/result").json()
    rq = next(x for x in r["questions"] if x["id"] == q["id"])
    assert rq["is_correct"] and rq["answer"] == {"key": key_display} and rq["response"] == {"key": key_display}
    assert [o["label"] for o in rq["options"]] == ["A", "B", "C", "D"]
