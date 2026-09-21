from datetime import timedelta

from sqlalchemy import select

from app.core.security import now
from app.models import Question, Topic
from tests.factories import PASSWORD, make_user
from tests.test_exams_api import bank_ready


def exam_with_questions(client, db, mcq=4, tf=1, short=1, essay=False):
    admin, topics = bank_ready(client, db)
    exam = client.post("/api/exams", json={"title": "Kiểm tra"}).json()
    ids = []
    for qtype, n in (("mcq", mcq), ("true_false", tf), ("short_answer", short)):
        if n:
            ids += [q["id"] for q in client.get("/api/questions", params={"type": qtype, "page_size": n}).json()["items"]][:n]
    if essay:
        e = client.post("/api/questions", json={"type": "essay", "stem": "Chứng minh bất đẳng thức", "solution": "…", "answer": {"text": "Mẫu"}}).json()
        ids.append(e["id"])
    exam = client.post(f"/api/exams/{exam['id']}/questions", json={"question_ids": ids}).json()
    return admin, exam


def klass_with_student(client, db, admin, username="hs01"):
    student = make_user(db, admin.organization, username, role="student", full_name="Học Sinh")
    db.commit()
    c = client.post("/api/classes", json={"name": f"10A1-{username}"}).json()
    client.post(f"/api/classes/{c['id']}/members", json={"user_ids": [str(student.id)]})
    return c, student


def assign(client, exam_id, class_id, minutes=45, open_delta=-60, close_delta=3600, **kw):
    body = {"exam_id": exam_id, "open_at": (now() + timedelta(seconds=open_delta)).isoformat(),
            "close_at": (now() + timedelta(seconds=close_delta)).isoformat(), "duration_minutes": minutes, "class_ids": [class_id], **kw}
    r = client.post("/api/assignments", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def login(client, org_code, username):
    c = client.__class__(client.app)
    r = c.post("/api/auth/login", json={"org_code": org_code, "username": username, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return c


def key_of(db, qid):
    return db.get(Question, qid).answer
