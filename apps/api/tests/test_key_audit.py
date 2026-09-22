from datetime import timedelta

from sqlalchemy import select

from app.shared.domain.clock import utcnow as now
from app.modules.bank.domain.entities import Question
from app.modules.bank.domain.services.key_audit import evidence_for
from tests.exam_helpers import assign, display_key, exam_with_questions, klass_with_student, login


def test_rule_on_synthetic_rows():
    good = [({"key": "B"}, 0.9)] * 4 + [({"key": "C"}, 0.3)] * 6  # best students choose B, key says A
    ev = evidence_for(good, "A")
    assert ev and ev["top_quartile"]["choice"] == "B" and "nhóm giỏi chọn B" in ev["reason"]
    hard = [({"key": "A"}, 0.95)] * 3 + [({"key": x}, 0.3) for x in "BCDBCDBCD"]  # hard but correct
    assert evidence_for(hard, "A") is None
    assert evidence_for(good[:5], "A") is None  # not enough answers


def test_wrong_key_flagged_end_to_end_then_fixed(client, db):
    admin, exam = exam_with_questions(client, db, mcq=4, tf=0, short=0)
    klass, _ = klass_with_student(client, db, admin, "hs00")
    target = exam["questions"][0]["id"]
    q = db.get(Question, target)
    true_key = q.answer["key"]
    wrong = next(o["label"] for o in q.options if o["label"] != true_key)
    q.answer = {"key": wrong}  # the bank's key is wrong
    db.commit()
    for i in range(1, 12):
        klass_with_student(client, db, admin, f"hsx{i}")
        client.post(f"/api/classes/{klass['id']}/members", json={"user_ids": [client.post('/api/users/search', json={'q': f'hsx{i}'}).json()['data'][0]['id']]})
    a = assign(client, exam["id"], klass["id"])
    db.expire_all()
    for i in range(1, 12):
        s = login(client, "trungtama", f"hsx{i}")
        att = s.post(f"/api/assignments/{a['id']}/start").json()["attempt_id"]
        for vq in s.get(f"/api/attempts/{att}").json()["questions"]:
            if vq["id"] == target:
                # students pick what is really right (the original key)
                content = next(o["content"] for o in q.options if o["label"] == true_key)
                s.put(f"/api/attempts/{att}/answers/{target}", json={"response": {"key": next(o["label"] for o in vq["options"] if o["content"] == content)}})
            elif i <= 8:
                s.put(f"/api/attempts/{att}/answers/{vq['id']}", json={"response": display_key(db, vq)})
        s.post(f"/api/attempts/{att}/submit")
    r = client.post("/api/review/key-audit").json()
    assert r["flagged"] == [target]
    db.expire_all()
    flagged = db.get(Question, target)
    assert flagged.status == "flagged" and "Nghi sai đáp án" in flagged.issues
    listed = client.post("/api/review/flagged/search", json={}).json()["data"]
    assert listed[0]["flag_evidence"]["top_quartile"]["choice"] == true_key
    # excluded from new exams
    new_exam = client.post("/api/exams", json={"title": "x"}).json()
    r = client.post(f"/api/exams/{new_exam['id']}/questions", json={"question_ids": [target]})
    assert r.status_code == 422
    # teacher fixes the key and approves
    client.patch(f"/api/questions/{target}", json={"answer": {"key": true_key}})
    assert client.post(f"/api/review/questions/{target}/action", json={"action": "approve"}).json()["status"] == "approved"
    assert client.post("/api/review/key-audit").json()["flagged"] == []
