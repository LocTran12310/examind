from sqlalchemy import select

from app.models import Topic
from tests.test_documents_api import run_jobs, sample, upload
from tests.test_review_api import setup_admin


def bank_ready(client, db):
    admin = setup_admin(client, db)
    for name in ("de-mau-toan10.docx", "de-thpt2025-toan.docx"):
        upload(client, name, sample(name))
    run_jobs()
    topics = {t.name: str(t.id) for t in db.scalars(select(Topic).where(Topic.organization_id == admin.organization_id))}
    return admin, topics


def test_blueprint_draws_distinct_questions_and_reports_shortfalls(client, db):
    _, t = bank_ready(client, db)
    exam = client.post("/api/exams", json={"title": "Kiểm tra 15 phút"}).json()
    rows = [{"topic_id": t["Đại số"], "type": "mcq", "count": 6}, {"topic_id": t["Hình học"], "type": "mcq", "count": 4},
            {"topic_id": t["Xác suất"], "type": "mcq", "count": 3}]
    r = client.post(f"/api/exams/{exam['id']}/blueprint", json={"rows": rows, "seed": 1}).json()
    assert r["added"] == 10 and r["shortfalls"] == [{"row": 2, "missing": 3}]
    e = r["exam"]
    ids = [q["id"] for q in e["questions"]]
    assert len(set(ids)) == 10 and e["total_points"] == 2.5
    assert [q["position"] for q in e["questions"]] == list(range(1, 11))
    assert all(q["section"] == "I" and q["answer"] for q in e["questions"])


def test_manual_edits_points_and_sections(client, db):
    _, t = bank_ready(client, db)
    exam = client.post("/api/exams", json={"title": "Đề hỗn hợp"}).json()
    tf = client.get("/api/questions", params={"type": "true_false"}).json()["items"][:2]
    mcq = client.get("/api/questions", params={"type": "mcq", "q": "parabol"}).json()["items"][:2]
    e = client.post(f"/api/exams/{exam['id']}/questions", json={"question_ids": [x["id"] for x in tf + mcq]}).json()
    assert [q["section"] for q in e["questions"]] == ["I", "I", "II", "II"] and e["total_points"] == 2.5
    e = client.patch(f"/api/exams/{exam['id']}", json={"settings": {"points_by_type": {"mcq": 0.5}}}).json()
    assert e["total_points"] == 3.0
    first = e["questions"][0]["id"]
    e = client.patch(f"/api/exams/{exam['id']}/questions/{first}", json={"points": 2}).json()
    assert e["total_points"] == 4.5
    order = [q["id"] for q in e["questions"]][::-1]
    assert [q["id"] for q in client.put(f"/api/exams/{exam['id']}/order", json={"question_ids": order}).json()["questions"]] == order
    e = client.delete(f"/api/exams/{exam['id']}/questions/{first}").json()
    assert e["question_count"] == 3
    swapped = client.post(f"/api/exams/{exam['id']}/questions/{order[0]}/swap").json()
    assert order[0] not in [q["id"] for q in swapped["questions"]] and swapped["question_count"] == 3


def test_question_in_exam_cannot_be_deleted_and_list(client, db):
    _, t = bank_ready(client, db)
    exam = client.post("/api/exams", json={"title": "Đề"}).json()
    q = client.get("/api/questions").json()["items"][0]
    client.post(f"/api/exams/{exam['id']}/questions", json={"question_ids": [q["id"]]})
    r = client.delete(f"/api/questions/{q['id']}")
    assert r.status_code == 409 and r.json()["error"]["code"] == "question_in_use"
    listed = client.get("/api/exams").json()["items"]
    assert listed[0]["question_count"] == 1 and listed[0]["questions"] == []
    assert client.post("/api/exams", json={"title": " "}).status_code == 422
